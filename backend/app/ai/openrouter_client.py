import asyncio
import httpx
import json
import re
from typing import Dict, Any, List
from loguru import logger


def _strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` wrappers that models emit despite JSON-mode prompts."""
    if not isinstance(text, str):
        return text
    t = text.strip()
    # ```json {...} ``` or ``` {...} ```
    m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", t, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return t


def _extract_json(text: str) -> Dict[str, Any]:
    """Best-effort parse: direct loads, then first {...} substring."""
    cleaned = _strip_code_fences(text)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        return {"text": text}
    except json.JSONDecodeError:
        pass
    # Fallback: find first JSON object in free text
    try:
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            parsed = json.loads(m.group(0))
            if isinstance(parsed, dict):
                return parsed
    except Exception:
        pass
    return {"text": text}


class OpenRouterClient:
    """
    OpenRouter API Client for LeadHunter AI.
    Created by harsh0o.
    """

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1", model: str = "mistralai/mistral-7b-instruct:free"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://leadhunter.ai",
            "X-Title": "LeadHunter AI"
        }

    async def chat_completion(self, system_prompt: str, user_message: str, temperature: float = 0.1, max_tokens: int = 1000) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # Only send response_format when JSON mode is actually wanted; None breaks some gateways
        want_json = temperature < 0.2
        if want_json:
            payload["response_format"] = {"type": "json_object"}

        retries = 3
        backoff = 2
        stripped_format_and_retried = False

        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(retries):
                try:
                    logger.debug(f"OpenRouter Request: {self.model}, attempt {attempt+1}")
                    response = await client.post(url, headers=self.headers, json=payload)

                    if response.status_code == 429:
                        wait = backoff ** (attempt + 1)
                        logger.warning(f"Rate limited by OpenRouter. Waiting {wait}s...")
                        await asyncio.sleep(wait)
                        continue

                    # Do not retry client errors (bad key, bad model, bad payload) -
                    # except response_format 400s which may work without strict JSON mode.
                    if 400 <= response.status_code < 500:
                        if (
                            want_json
                            and not stripped_format_and_retried
                            and response.status_code == 400
                            and "response_format" in payload
                        ):
                            logger.warning("response_format rejected; retrying once without it")
                            del payload["response_format"]
                            stripped_format_and_retried = True
                            continue
                        response.raise_for_status()

                    response.raise_for_status()
                    try:
                        data = response.json()
                    except Exception as e:
                        logger.error(f"OpenRouter returned non-JSON: {e}")
                        if attempt == retries - 1:
                            raise
                        await asyncio.sleep(backoff ** (attempt + 1))
                        continue

                    try:
                        content = data["choices"][0]["message"]["content"]
                    except (KeyError, IndexError, TypeError) as e:
                        logger.error(f"OpenRouter unexpected shape: {e} keys={list(data.keys()) if isinstance(data, dict) else type(data)}")
                        if attempt == retries - 1:
                            raise ValueError(f"OpenRouter unexpected response shape: {str(data)[:300]}")
                        await asyncio.sleep(backoff ** (attempt + 1))
                        continue

                    # Attempt to parse as JSON if we expect JSON (handles ```json fences)
                    return _extract_json(content)

                except (httpx.HTTPStatusError, httpx.RequestError) as e:
                    status = getattr(getattr(e, "response", None), "status_code", None)
                    # Never retry 401/402/403/404 (auth/quota/model errors) - fail fast
                    if status is not None and 400 <= status < 500 and status != 429:
                        logger.error(f"OpenRouter client error {status}, not retrying: {e}")
                        raise
                    logger.error(f"OpenRouter API Error: {e}")
                    if attempt == retries - 1:
                        raise e
                    await asyncio.sleep(backoff ** (attempt + 1))

        # Exhausted retries (e.g. repeated 429s) – raise so callers don't silently drop leads
        raise RuntimeError("OpenRouter request failed after retries (rate-limited or unavailable)")

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/models")
                return response.status_code == 200
        except Exception:
            return False

    async def get_available_free_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/models")
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    free_models = [
                        m["id"] for m in models
                        if float(m.get("pricing", {}).get("prompt", -1)) == 0.0
                        and float(m.get("pricing", {}).get("completion", -1)) == 0.0
                    ]
                    return free_models
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
        return []
