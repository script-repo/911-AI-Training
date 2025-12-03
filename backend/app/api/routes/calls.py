"""REST API routes for call management"""

import logging
from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import schemas
from app.models.database import (
    CallSession,
    CallTranscript,
    TrainingScenario,
    CallSessionStatus,
    DifficultyLevel
)
from app.services.dialogue_manager import dialogue_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["calls"])


@router.post("/calls/start", response_model=schemas.CallSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_call_session(
    request: schemas.CallSessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new call training session.

    Creates a new call session and initializes the conversation context.
    """
    try:
        # Verify scenario exists
        result = await db.execute(
            select(TrainingScenario).where(TrainingScenario.id == request.scenario_id)
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training scenario not found: {request.scenario_id}"
            )

        # Create new call session
        call_session = CallSession(
            operator_id=request.operator_id,
            scenario_id=request.scenario_id,
            status=CallSessionStatus.ACTIVE,
            started_at=datetime.utcnow()
        )

        db.add(call_session)
        await db.commit()
        await db.refresh(call_session)

        # Initialize dialogue context
        await dialogue_manager.create_session_context(
            session_id=str(call_session.id),
            scenario_data={
                "id": str(scenario.id),
                "name": scenario.name,
                "description": scenario.description,
                "scenario_script": scenario.scenario_script,
                "difficulty_level": scenario.difficulty_level.value
            },
            caller_profile=scenario.caller_profile
        )

        logger.info(f"Call session started: {call_session.id}")

        return call_session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start call session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start call session: {str(e)}"
        )


@router.get("/calls/{call_id}", response_model=schemas.CallSessionResponse)
async def get_call_session(
    call_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific call session.
    """
    try:
        result = await db.execute(
            select(CallSession).where(CallSession.id == call_id)
        )
        call_session = result.scalar_one_or_none()

        if not call_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Call session not found: {call_id}"
            )

        return call_session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get call session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get call session: {str(e)}"
        )


@router.post("/calls/{call_id}/end", response_model=schemas.CallSessionResponse)
async def end_call_session(
    call_id: UUID,
    request: schemas.CallSessionEnd,
    db: AsyncSession = Depends(get_db)
):
    """
    End a call training session.

    Marks the session as completed and calculates duration.
    """
    try:
        # Get call session
        result = await db.execute(
            select(CallSession).where(CallSession.id == call_id)
        )
        call_session = result.scalar_one_or_none()

        if not call_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Call session not found: {call_id}"
            )

        if call_session.status != CallSessionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Call session is not active: {call_session.status}"
            )

        # Update session
        ended_at = datetime.utcnow()
        duration_ms = int((ended_at - call_session.started_at).total_seconds() * 1000)

        # Update metadata with notes if provided
        metadata = call_session.metadata or {}
        if request.notes:
            metadata["notes"] = request.notes
        if request.operator_feedback:
            metadata["operator_feedback"] = request.operator_feedback

        stmt = update(CallSession).where(
            CallSession.id == call_id
        ).values(
            status=CallSessionStatus.COMPLETED,
            ended_at=ended_at,
            duration_ms=duration_ms,
            metadata=metadata
        )
        await db.execute(stmt)
        await db.commit()

        # Refresh to get updated values
        await db.refresh(call_session)

        # Clean up dialogue context
        await dialogue_manager.delete_session_context(str(call_id))

        logger.info(f"Call session ended: {call_id}, duration: {duration_ms}ms")

        return call_session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end call session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end call session: {str(e)}"
        )


@router.get("/calls/{call_id}/transcript", response_model=schemas.TranscriptListResponse)
async def get_call_transcript(
    call_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get full transcript for a call session.
    """
    try:
        # Verify session exists
        result = await db.execute(
            select(CallSession).where(CallSession.id == call_id)
        )
        call_session = result.scalar_one_or_none()

        if not call_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Call session not found: {call_id}"
            )

        # Get transcripts
        result = await db.execute(
            select(CallTranscript)
            .where(CallTranscript.session_id == call_id)
            .order_by(CallTranscript.timestamp_ms)
        )
        transcripts = result.scalars().all()

        return schemas.TranscriptListResponse(
            session_id=call_id,
            transcripts=transcripts,
            total_count=len(transcripts)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get call transcript: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get call transcript: {str(e)}"
        )


@router.get("/scenarios", response_model=schemas.TrainingScenarioListResponse)
async def list_scenarios(
    difficulty: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List available training scenarios.

    Optionally filter by difficulty level.
    """
    try:
        # Build query
        query = select(TrainingScenario)

        if difficulty:
            try:
                difficulty_enum = DifficultyLevel(difficulty.lower())
                query = query.where(TrainingScenario.difficulty_level == difficulty_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid difficulty level: {difficulty}"
                )

        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        scenarios = result.scalars().all()

        # Get total count
        count_query = select(TrainingScenario)
        if difficulty:
            count_query = count_query.where(
                TrainingScenario.difficulty_level == DifficultyLevel(difficulty.lower())
            )
        count_result = await db.execute(count_query)
        total_count = len(count_result.scalars().all())

        return schemas.TrainingScenarioListResponse(
            scenarios=scenarios,
            total_count=total_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list scenarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scenarios: {str(e)}"
        )


@router.post("/scenarios", response_model=schemas.TrainingScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    request: schemas.TrainingScenarioCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new training scenario.
    """
    try:
        # Check if scenario with same name exists
        result = await db.execute(
            select(TrainingScenario).where(TrainingScenario.name == request.name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Scenario with name '{request.name}' already exists"
            )

        # Create scenario
        scenario = TrainingScenario(
            name=request.name,
            description=request.description,
            caller_profile=request.caller_profile.model_dump(),
            scenario_script=request.scenario_script.model_dump(),
            difficulty_level=DifficultyLevel(request.difficulty_level),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(scenario)
        await db.commit()
        await db.refresh(scenario)

        logger.info(f"Training scenario created: {scenario.id} - {scenario.name}")

        return scenario

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create scenario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scenario: {str(e)}"
        )


@router.get("/scenarios/{scenario_id}", response_model=schemas.TrainingScenarioResponse)
async def get_scenario(
    scenario_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific training scenario.
    """
    try:
        result = await db.execute(
            select(TrainingScenario).where(TrainingScenario.id == scenario_id)
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training scenario not found: {scenario_id}"
            )

        return scenario

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scenario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scenario: {str(e)}"
        )
