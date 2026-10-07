from loguru import logger
from app.ai.openrouter_client import OpenRouterClient
from app.ai.prompts import DRAFT_GENERATOR_SYSTEM_PROMPT, DRAFT_GENERATOR_USER_TEMPLATE

class DraftGenerator:
    """
    Agent 3: Drafts Cover Letters and Cold DMs.
    Created by harsh0o.
    """
    def __init__(self, client: OpenRouterClient):
        self.client = client

    async def generate(
        self, 
        lead_summary: str, 
        persona: str, 
        user_name: str, 
        draft_type: str, 
        tone: str, 
        custom_instructions: str = ''
    ) -> str:
        user_msg = DRAFT_GENERATOR_USER_TEMPLATE.format(
            lead_summary=lead_summary,
            persona=persona,
            user_name=user_name,
            draft_type=draft_type,
            tone=tone,
            custom_instructions=custom_instructions
        )
        
        try:
            # We don't expect JSON object here, just pure text
            resp = await self.client.chat_completion(
                system_prompt=DRAFT_GENERATOR_SYSTEM_PROMPT,
                user_message=user_msg,
                temperature=0.7,
                max_tokens=2000
            )
            
            if isinstance(resp, dict) and "text" in resp and isinstance(resp["text"], str):
                text = resp["text"].strip()
                if not text:
                    raise ValueError("Empty draft text from AI")
                return text

            # If model returned JSON despite text mode, extract a text field if present
            if isinstance(resp, dict):
                for k in ("draft", "content", "message", "result"):
                    v = resp.get(k)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
            raise ValueError(f"Unexpected draft response shape: {str(resp)[:300]}")
            
        except Exception as e:
            logger.error(f"Error in DraftGenerator: {e}")
            raise
