"""Dialogue manager for conversation context and state management"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class DialogueManager:
    """Manages conversation context and state for call sessions"""

    def __init__(self):
        self.redis_client = None

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("DialogueManager initialized with Redis connection")
        except Exception as e:
            logger.error(f"Failed to initialize DialogueManager: {e}")
            raise

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("DialogueManager Redis connection closed")

    async def create_session_context(
        self,
        session_id: str,
        scenario_data: Dict[str, Any],
        caller_profile: Dict[str, Any]
    ) -> None:
        """
        Create initial conversation context for a session.

        Args:
            session_id: Call session ID
            scenario_data: Scenario configuration
            caller_profile: Caller profile information
        """
        try:
            context = {
                "session_id": session_id,
                "scenario": scenario_data,
                "caller_profile": caller_profile,
                "conversation_history": [],
                "current_emotional_state": caller_profile.get("initial_emotional_state", "calm"),
                "extracted_entities": {},
                "key_info_revealed": [],
                "started_at": datetime.utcnow().isoformat(),
                "turn_count": 0
            }

            key = f"session:{session_id}:context"
            await self.redis_client.set(
                key,
                json.dumps(context),
                ex=settings.session_ttl
            )

            logger.info(f"Session context created: {session_id}")

        except Exception as e:
            logger.error(f"Failed to create session context: {e}")
            raise

    async def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session context.

        Args:
            session_id: Call session ID

        Returns:
            Session context dict or None if not found
        """
        try:
            key = f"session:{session_id}:context"
            data = await self.redis_client.get(key)

            if data:
                return json.loads(data)
            else:
                logger.warning(f"Session context not found: {session_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to get session context: {e}")
            return None

    async def update_session_context(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> None:
        """
        Update session context with new information.

        Args:
            session_id: Call session ID
            updates: Dictionary of fields to update
        """
        try:
            context = await self.get_session_context(session_id)
            if not context:
                raise ValueError(f"Session context not found: {session_id}")

            # Update context
            context.update(updates)

            key = f"session:{session_id}:context"
            await self.redis_client.set(
                key,
                json.dumps(context),
                ex=settings.session_ttl
            )

            logger.debug(f"Session context updated: {session_id}")

        except Exception as e:
            logger.error(f"Failed to update session context: {e}")
            raise

    async def add_conversation_turn(
        self,
        session_id: str,
        speaker: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a conversation turn to history.

        Args:
            session_id: Call session ID
            speaker: "operator" or "caller"
            text: Utterance text
            metadata: Optional metadata
        """
        try:
            context = await self.get_session_context(session_id)
            if not context:
                raise ValueError(f"Session context not found: {session_id}")

            turn = {
                "role": "assistant" if speaker == "caller" else "user",
                "content": text,
                "speaker": speaker,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }

            context["conversation_history"].append(turn)
            context["turn_count"] = len(context["conversation_history"])

            await self.update_session_context(session_id, context)

        except Exception as e:
            logger.error(f"Failed to add conversation turn: {e}")
            raise

    async def get_conversation_history(
        self,
        session_id: str,
        max_turns: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.

        Args:
            session_id: Call session ID
            max_turns: Optional limit on number of turns to return

        Returns:
            List of conversation turns
        """
        try:
            context = await self.get_session_context(session_id)
            if not context:
                return []

            history = context.get("conversation_history", [])

            if max_turns:
                return history[-max_turns:]
            else:
                return history

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []

    async def update_emotional_state(
        self,
        session_id: str,
        emotional_state: str
    ) -> None:
        """
        Update caller's emotional state.

        Args:
            session_id: Call session ID
            emotional_state: New emotional state
        """
        try:
            await self.update_session_context(
                session_id,
                {"current_emotional_state": emotional_state}
            )
            logger.info(f"Emotional state updated to '{emotional_state}' for session {session_id}")

        except Exception as e:
            logger.error(f"Failed to update emotional state: {e}")
            raise

    async def add_extracted_entity(
        self,
        session_id: str,
        entity_type: str,
        entity_value: str
    ) -> None:
        """
        Add extracted entity to session context.

        Args:
            session_id: Call session ID
            entity_type: Type of entity
            entity_value: Entity value
        """
        try:
            context = await self.get_session_context(session_id)
            if not context:
                raise ValueError(f"Session context not found: {session_id}")

            if entity_type not in context["extracted_entities"]:
                context["extracted_entities"][entity_type] = []

            if entity_value not in context["extracted_entities"][entity_type]:
                context["extracted_entities"][entity_type].append(entity_value)

            await self.update_session_context(session_id, context)

        except Exception as e:
            logger.error(f"Failed to add extracted entity: {e}")
            raise

    async def delete_session_context(self, session_id: str) -> None:
        """
        Delete session context (called when session ends).

        Args:
            session_id: Call session ID
        """
        try:
            key = f"session:{session_id}:context"
            await self.redis_client.delete(key)
            logger.info(f"Session context deleted: {session_id}")

        except Exception as e:
            logger.error(f"Failed to delete session context: {e}")


# Global service instance
dialogue_manager = DialogueManager()
