from loguru import logger
from app.ai.openrouter_client import OpenRouterClient
from app.ai.prompts import INTENT_BOUNCER_SYSTEM_PROMPT, INTENT_BOUNCER_USER_TEMPLATE
from app.models.raw_post import IntentClassification, IntentType

class IntentBouncer:
    """
    Agent 1: Classifies the intent of raw posts.
    Created by harsh0o.
    """
    def __init__(self, client: OpenRouterClient):
        self.client = client

    async def classify(self, post_text: str) -> IntentClassification:
        user_msg = INTENT_BOUNCER_USER_TEMPLATE.format(post_text=post_text)
        
        try:
            resp = await self.client.chat_completion(
                system_prompt=INTENT_BOUNCER_SYSTEM_PROMPT,
                user_message=user_msg,
                temperature=0.1
            )
            
            if "intent" in resp and "confidence" in resp:
                raw_intent = str(resp["intent"]).strip().upper().replace("-", "_").replace(" ", "_")
                try:
                    intent_enum = IntentType(raw_intent)
                except ValueError:
                    intent_enum = IntentType.UNCLEAR
                try:
                    conf = float(resp["confidence"])
                except (TypeError, ValueError):
                    conf = 0.0
                conf = max(0.0, min(1.0, conf))
                result = IntentClassification(
                    intent=intent_enum,
                    confidence=conf,
                    reasoning=str(resp.get("reasoning", "") or "")
                )
                logger.debug(f"Classified intent: {result.intent} with conf {result.confidence}")
                return result
                
        except Exception as e:
            logger.error(f"Error in IntentBouncer: {e}")
            
        return IntentClassification(intent=IntentType.UNCLEAR, confidence=0.0, reasoning="Parsing failed.")

    def is_passing(self, result: IntentClassification, threshold: float = 0.80) -> bool:
        return result.intent == IntentType.OFFERING_JOB and result.confidence >= threshold
