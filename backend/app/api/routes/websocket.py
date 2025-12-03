"""WebSocket endpoint for real-time call simulation"""

import logging
import json
from typing import Dict, Any
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db, AsyncSessionLocal
from app.models import schemas
from app.services.llm_service import llm_service
from app.services.tts_service import tts_service
from app.services.nlp_service import nlp_service
from app.services.audio_service import audio_service
from app.services.dialogue_manager import dialogue_manager
from app.models.database import CallSession, CallTranscript, ExtractedEntity, Speaker

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        """Disconnect a WebSocket client"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")

    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Send message to specific session"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {session_id}: {e}")

    async def broadcast(self, session_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections for a session"""
        await self.send_message(session_id, message)


manager = ConnectionManager()


@router.websocket("/ws/call/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for real-time call simulation.

    Handles:
    - Audio streaming (base64 encoded chunks)
    - Control messages (mute, hold, terminate)
    - Transcript updates
    - Entity extraction updates
    - Emotional state updates
    """
    await manager.connect(session_id, websocket)

    # Get database session using context manager
    async with AsyncSessionLocal() as db:
        try:
            # Verify session exists
            from sqlalchemy import select
            result = await db.execute(
                select(CallSession).where(CallSession.id == UUID(session_id))
            )
            call_session = result.scalar_one_or_none()

            if not call_session:
                await websocket.send_json({
                    "type": "error",
                    "error_code": "SESSION_NOT_FOUND",
                    "error_message": f"Call session not found: {session_id}"
                })
                await websocket.close()
                return

            # Get session context
            context = await dialogue_manager.get_session_context(session_id)
            if not context:
                await websocket.send_json({
                    "type": "error",
                    "error_code": "CONTEXT_NOT_FOUND",
                    "error_message": "Session context not found"
                })
                await websocket.close()
                return

            # Send initial greeting from AI caller
            await send_initial_greeting(websocket, session_id, context, db)

            # Main message loop
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                message_type = message.get("type")

                if message_type == "audio_chunk":
                    await handle_audio_chunk(message, session_id, context, websocket, db)

                elif message_type == "control":
                    await handle_control_message(message, session_id, websocket, db)

                elif message_type == "transcript":
                    await handle_transcript_message(message, session_id, context, websocket, db)

                else:
                    logger.warning(f"Unknown message type: {message_type}")

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {session_id}")
            manager.disconnect(session_id)

        except Exception as e:
            logger.error(f"WebSocket error for session {session_id}: {e}")
            try:
                await websocket.send_json({
                    "type": "error",
                    "error_code": "INTERNAL_ERROR",
                    "error_message": str(e)
                })
            except:
                pass
            manager.disconnect(session_id)


async def send_initial_greeting(
    websocket: WebSocket,
    session_id: str,
    context: Dict[str, Any],
    db: AsyncSession
):
    """Send initial greeting from AI caller"""
    try:
        # Get initial situation from scenario
        scenario = context.get("scenario", {})
        initial_situation = scenario.get("scenario_script", {}).get("initial_situation", "")

        # Generate initial caller statement
        conversation_history = []
        caller_profile = context.get("caller_profile", {})

        llm_response = await llm_service.generate_caller_response(
            conversation_history=[],
            caller_profile=caller_profile,
            scenario_context=scenario.get("scenario_script", {}),
            current_emotional_state=context.get("current_emotional_state", "calm")
        )

        # Generate speech
        tts_response = await tts_service.synthesize_speech(
            text=llm_response["response_text"],
            emotional_state=llm_response["emotional_state"]
        )

        # Save transcript
        transcript = CallTranscript(
            session_id=UUID(session_id),
            timestamp_ms=0,
            speaker=Speaker.CALLER,
            text=llm_response["response_text"],
            emotional_state=llm_response["emotional_state"],
            confidence_score=llm_response.get("confidence", 0.9)
        )
        db.add(transcript)
        await db.commit()
        await db.refresh(transcript)

        # Extract entities
        await extract_and_save_entities(llm_response["response_text"], transcript.id, session_id, db, websocket)

        # Update dialogue manager
        await dialogue_manager.add_conversation_turn(
            session_id,
            "caller",
            llm_response["response_text"]
        )
        await dialogue_manager.update_emotional_state(
            session_id,
            llm_response["emotional_state"]
        )

        # Send to client
        await websocket.send_json({
            "type": "transcript_update",
            "session_id": session_id,
            "transcript_id": str(transcript.id),
            "speaker": "caller",
            "text": llm_response["response_text"],
            "timestamp_ms": 0,
            "confidence_score": llm_response.get("confidence", 0.9)
        })

        await websocket.send_json({
            "type": "audio_chunk",
            "session_id": session_id,
            "audio_data": tts_response["audio_data"],
            "timestamp_ms": 0,
            "duration_ms": tts_response["duration_ms"]
        })

        await websocket.send_json({
            "type": "emotional_state",
            "session_id": session_id,
            "state": llm_response["emotional_state"],
            "intensity": 0.7,
            "timestamp_ms": 0
        })

    except Exception as e:
        logger.error(f"Failed to send initial greeting: {e}")
        raise


async def handle_audio_chunk(
    message: Dict[str, Any],
    session_id: str,
    context: Dict[str, Any],
    websocket: WebSocket,
    db: AsyncSession
):
    """Handle incoming audio chunk from operator"""
    try:
        audio_data = message.get("audio_data")
        timestamp_ms = message.get("timestamp_ms", 0)

        # Validate audio chunk
        if not audio_service.validate_audio_chunk(audio_data):
            await websocket.send_json({
                "type": "error",
                "error_code": "INVALID_AUDIO",
                "error_message": "Invalid audio chunk"
            })
            return

        # In a real implementation, you would:
        # 1. Use speech-to-text to transcribe operator audio
        # 2. For now, we'll assume transcript is sent separately

        logger.debug(f"Received audio chunk for session {session_id}")

    except Exception as e:
        logger.error(f"Error handling audio chunk: {e}")


async def handle_transcript_message(
    message: Dict[str, Any],
    session_id: str,
    context: Dict[str, Any],
    websocket: WebSocket,
    db: AsyncSession
):
    """Handle transcript message (operator speech)"""
    try:
        text = message.get("text", "")
        timestamp_ms = message.get("timestamp_ms", 0)

        if not text:
            return

        # Save operator transcript
        transcript = CallTranscript(
            session_id=UUID(session_id),
            timestamp_ms=timestamp_ms,
            speaker=Speaker.OPERATOR,
            text=text,
            confidence_score=0.95
        )
        db.add(transcript)
        await db.commit()
        await db.refresh(transcript)

        # Extract entities from operator speech
        await extract_and_save_entities(text, transcript.id, session_id, db, websocket)

        # Update conversation history
        await dialogue_manager.add_conversation_turn(session_id, "operator", text)

        # Generate AI caller response
        conversation_history = await dialogue_manager.get_conversation_history(session_id, max_turns=10)
        caller_profile = context.get("caller_profile", {})
        scenario_context = context.get("scenario", {}).get("scenario_script", {})
        current_emotional_state = context.get("current_emotional_state", "calm")

        llm_response = await llm_service.generate_caller_response(
            conversation_history=conversation_history,
            caller_profile=caller_profile,
            scenario_context=scenario_context,
            current_emotional_state=current_emotional_state
        )

        # Generate speech for caller response
        tts_response = await tts_service.synthesize_speech(
            text=llm_response["response_text"],
            emotional_state=llm_response["emotional_state"]
        )

        # Save caller transcript
        caller_transcript = CallTranscript(
            session_id=UUID(session_id),
            timestamp_ms=timestamp_ms + 1000,  # Add small delay
            speaker=Speaker.CALLER,
            text=llm_response["response_text"],
            emotional_state=llm_response["emotional_state"],
            confidence_score=llm_response.get("confidence", 0.9)
        )
        db.add(caller_transcript)
        await db.commit()
        await db.refresh(caller_transcript)

        # Extract entities from caller response
        await extract_and_save_entities(
            llm_response["response_text"],
            caller_transcript.id,
            session_id,
            db,
            websocket
        )

        # Update dialogue manager
        await dialogue_manager.add_conversation_turn(
            session_id,
            "caller",
            llm_response["response_text"]
        )
        await dialogue_manager.update_emotional_state(
            session_id,
            llm_response["emotional_state"]
        )

        # Send responses to client
        await websocket.send_json({
            "type": "transcript_update",
            "session_id": session_id,
            "transcript_id": str(caller_transcript.id),
            "speaker": "caller",
            "text": llm_response["response_text"],
            "timestamp_ms": timestamp_ms + 1000,
            "confidence_score": llm_response.get("confidence", 0.9)
        })

        await websocket.send_json({
            "type": "audio_chunk",
            "session_id": session_id,
            "audio_data": tts_response["audio_data"],
            "timestamp_ms": timestamp_ms + 1000
        })

        await websocket.send_json({
            "type": "emotional_state",
            "session_id": session_id,
            "state": llm_response["emotional_state"],
            "intensity": 0.7,
            "timestamp_ms": timestamp_ms + 1000
        })

    except Exception as e:
        logger.error(f"Error handling transcript message: {e}")
        await websocket.send_json({
            "type": "error",
            "error_code": "PROCESSING_ERROR",
            "error_message": str(e)
        })


async def handle_control_message(
    message: Dict[str, Any],
    session_id: str,
    websocket: WebSocket,
    db: AsyncSession
):
    """Handle control messages (mute, hold, terminate)"""
    try:
        action = message.get("action")
        logger.info(f"Control action '{action}' for session {session_id}")

        if action == "terminate":
            # Update session status
            from sqlalchemy import select, update
            from app.models.database import CallSessionStatus
            from datetime import datetime

            stmt = update(CallSession).where(
                CallSession.id == UUID(session_id)
            ).values(
                status=CallSessionStatus.TERMINATED,
                ended_at=datetime.utcnow()
            )
            await db.execute(stmt)
            await db.commit()

            # Clean up session context
            await dialogue_manager.delete_session_context(session_id)

            await websocket.send_json({
                "type": "control_ack",
                "action": action,
                "status": "success"
            })

            # Close WebSocket
            await websocket.close()

        else:
            # Acknowledge other control actions
            await websocket.send_json({
                "type": "control_ack",
                "action": action,
                "status": "success"
            })

    except Exception as e:
        logger.error(f"Error handling control message: {e}")


async def extract_and_save_entities(
    text: str,
    transcript_id: UUID,
    session_id: str,
    db: AsyncSession,
    websocket: WebSocket
):
    """Extract entities from text and save to database"""
    try:
        # Extract entities
        extraction_result = await nlp_service.extract_entities(
            text=text,
            session_id=session_id,
            timestamp_ms=0
        )

        # Save entities to database
        for entity_data in extraction_result.get("entities", []):
            entity = ExtractedEntity(
                transcript_id=transcript_id,
                entity_type=entity_data["entity_type"],
                entity_value=entity_data["entity_value"],
                confidence_score=entity_data["confidence_score"],
                start_char=entity_data["start_char"],
                end_char=entity_data["end_char"],
                metadata=entity_data.get("metadata", {})
            )
            db.add(entity)

            # Update dialogue manager
            await dialogue_manager.add_extracted_entity(
                session_id,
                entity_data["entity_type"],
                entity_data["entity_value"]
            )

            # Send entity update to client
            await websocket.send_json({
                "type": "entity_update",
                "session_id": session_id,
                "entity_id": str(entity.id),
                "entity_type": entity_data["entity_type"],
                "entity_value": entity_data["entity_value"],
                "confidence_score": entity_data["confidence_score"]
            })

        await db.commit()

    except Exception as e:
        logger.error(f"Error extracting and saving entities: {e}")
