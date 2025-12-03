"""OpenRouter LLM integration service for AI caller responses"""

import logging
from typing import Dict, Any, List, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with OpenRouter LLM API"""

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.llm_base_url
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

    async def generate_caller_response(
        self,
        conversation_history: List[Dict[str, str]],
        caller_profile: Dict[str, Any],
        scenario_context: Dict[str, Any],
        current_emotional_state: str = "calm"
    ) -> Dict[str, Any]:
        """
        Generate AI caller response based on conversation context.

        Args:
            conversation_history: List of previous messages
            caller_profile: Caller's personality and background
            scenario_context: Current scenario information
            current_emotional_state: Current emotional state of caller

        Returns:
            Dict containing response text, emotional state, and metadata
        """
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(
                caller_profile,
                scenario_context,
                current_emotional_state
            )

            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)

            # Call OpenRouter API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                    }
                )
                response.raise_for_status()
                result = response.json()

            # Extract response
            response_text = result["choices"][0]["message"]["content"]

            # Analyze emotional state from response
            new_emotional_state = self._analyze_emotional_state(
                response_text,
                current_emotional_state
            )

            return {
                "response_text": response_text,
                "emotional_state": new_emotional_state,
                "confidence": 0.9,
                "metadata": {
                    "model": self.model,
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0)
                }
            }

        except httpx.HTTPError as e:
            logger.error(f"LLM API request failed: {e}")
            return self._get_fallback_response(current_emotional_state)
        except Exception as e:
            logger.error(f"Unexpected error in LLM service: {e}")
            return self._get_fallback_response(current_emotional_state)

    def _build_system_prompt(
        self,
        caller_profile: Dict[str, Any],
        scenario_context: Dict[str, Any],
        emotional_state: str
    ) -> str:
        """Build system prompt for LLM"""
        return f"""You are roleplaying as a 911 caller in a training simulation.

Caller Profile:
- Name: {caller_profile.get('name', 'Anonymous')}
- Age: {caller_profile.get('age', 'Unknown')}
- Background: {caller_profile.get('background_story', 'N/A')}
- Personality: {', '.join(caller_profile.get('personality_traits', []))}

Current Situation:
{scenario_context.get('initial_situation', '')}

Emergency Type: {scenario_context.get('emergency_type', 'Unknown')}
Location: {scenario_context.get('location_type', 'Unknown')}

Current Emotional State: {emotional_state}

Instructions:
1. Stay in character as the caller
2. Respond naturally and realistically to the operator's questions
3. Show appropriate emotion based on your current state
4. Gradually reveal information as the operator asks questions
5. Keep responses brief (1-3 sentences) as in a real emergency call
6. Show stress, fear, or confusion appropriate to the situation
7. Do not volunteer all information at once - make the operator work for it

Respond only as the caller would speak on the phone. Do not include stage directions or explanations."""

    def _analyze_emotional_state(
        self,
        response_text: str,
        current_state: str
    ) -> str:
        """
        Analyze emotional state from response text.

        In a production system, this would use sentiment analysis.
        For now, we use simple heuristics.
        """
        text_lower = response_text.lower()

        # Check for escalation indicators
        panic_words = ["help", "hurry", "dying", "bleeding", "can't breathe", "please"]
        calm_words = ["okay", "fine", "stable", "better", "calm"]

        panic_count = sum(1 for word in panic_words if word in text_lower)
        calm_count = sum(1 for word in calm_words if word in text_lower)

        # Determine state based on current state and indicators
        if panic_count > 2:
            return "panicked"
        elif panic_count > 0 or current_state in ["anxious", "panicked"]:
            return "anxious"
        elif calm_count > 0:
            return "calm"
        else:
            return current_state

    def _get_fallback_response(self, emotional_state: str) -> Dict[str, Any]:
        """Get fallback response if LLM fails"""
        fallback_responses = {
            "calm": "Yes, I understand. What do you need to know?",
            "anxious": "I... I'm trying to stay calm. What should I do?",
            "panicked": "Please help! I don't know what to do! Please hurry!"
        }

        return {
            "response_text": fallback_responses.get(emotional_state, "I... I need help."),
            "emotional_state": emotional_state,
            "confidence": 0.5,
            "metadata": {"fallback": True}
        }


# Global service instance
llm_service = LLMService()
