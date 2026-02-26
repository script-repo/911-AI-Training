"""Supervisor and admin API routes for call review, analytics, and management"""
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user, require_role
from app.db import get_db
from app.models.database import CallSession, CallTranscript, CallSessionStatus, TrainingScenario
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["supervisor"])


# --- Schemas ---

class CallHistoryItem(BaseModel):
    id: str
    operator_id: str
    operator_username: Optional[str] = None
    scenario_id: str
    scenario_name: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str

    class Config:
        from_attributes = True


class CallHistoryResponse(BaseModel):
    items: list[CallHistoryItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class TraineePerformanceSummary(BaseModel):
    user_id: str
    username: str
    total_calls: int
    completed_calls: int
    average_duration_ms: Optional[float] = None
    scenarios_attempted: int


class CallReviewComment(BaseModel):
    comment: str = Field(..., min_length=1, max_length=2000)


class SystemHealthResponse(BaseModel):
    active_calls: int
    total_calls: int
    total_scenarios: int
    total_users: int


# --- Endpoints ---

@router.get("/calls/history", response_model=CallHistoryResponse)
async def get_call_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    operator_id: Optional[str] = None,
    scenario_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get call history. Trainees see only their own calls.
    Supervisors and admins see all calls.
    """
    query = select(CallSession).options(selectinload(CallSession.scenario))

    # RBAC: trainees can only see their own calls
    if user.role == UserRole.TRAINEE:
        query = query.where(CallSession.operator_id == user.id)
    elif operator_id:
        query = query.where(CallSession.operator_id == UUID(operator_id))

    if scenario_id:
        query = query.where(CallSession.scenario_id == UUID(scenario_id))
    if status_filter:
        try:
            query = query.where(CallSession.status == CallSessionStatus(status_filter))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(desc(CallSession.started_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    sessions = result.scalars().all()

    items = []
    for s in sessions:
        items.append(CallHistoryItem(
            id=str(s.id),
            operator_id=str(s.operator_id) if s.operator_id else "unknown",
            scenario_id=str(s.scenario_id),
            scenario_name=s.scenario.name if s.scenario else None,
            started_at=s.started_at,
            ended_at=s.ended_at,
            duration_ms=s.duration_ms,
            status=s.status.value,
        ))

    return CallHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total,
    )


@router.get("/calls/{call_id}/metrics")
async def get_call_metrics(
    call_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get scoring metrics for a specific call."""
    # Verify access
    result = await db.execute(select(CallSession).where(CallSession.id == call_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Call not found")

    # RBAC check
    if user.role == UserRole.TRAINEE and session.operator_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Try to get computed score
    try:
        from app.models.protocol_event import CallScore
        score_result = await db.execute(
            select(CallScore).where(CallScore.call_id == call_id)
        )
        score = score_result.scalar_one_or_none()
        if score:
            return {
                "call_id": str(call_id),
                "total_score": score.total_score,
                "max_possible_score": score.max_possible_score,
                "subscores": score.subscores,
                "protocol_errors": score.protocol_errors,
                "feedback": score.feedback,
                "computed_at": score.computed_at.isoformat(),
            }
    except Exception:
        pass

    # Fallback: return basic metrics from performance_metrics table
    from app.models.database import PerformanceMetrics
    metrics_result = await db.execute(
        select(PerformanceMetrics).where(PerformanceMetrics.session_id == call_id)
    )
    metrics = metrics_result.scalars().all()

    return {
        "call_id": str(call_id),
        "total_score": None,
        "metrics": [
            {"name": m.metric_name, "value": m.metric_value, "measured_at": m.measured_at.isoformat()}
            for m in metrics
        ],
    }


@router.get("/trainees/{trainee_id}/performance", response_model=TraineePerformanceSummary)
async def get_trainee_performance(
    trainee_id: UUID,
    _supervisor: User = Depends(require_role(UserRole.SUPERVISOR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get performance summary for a specific trainee (supervisor/admin only)."""
    # Get user
    result = await db.execute(select(User).where(User.id == trainee_id))
    trainee = result.scalar_one_or_none()
    if not trainee:
        raise HTTPException(status_code=404, detail="Trainee not found")

    # Get call stats
    calls_result = await db.execute(
        select(CallSession).where(CallSession.operator_id == trainee_id)
    )
    calls = calls_result.scalars().all()

    completed = [c for c in calls if c.status == CallSessionStatus.COMPLETED]
    durations = [c.duration_ms for c in completed if c.duration_ms]
    scenario_ids = {c.scenario_id for c in calls}

    return TraineePerformanceSummary(
        user_id=str(trainee.id),
        username=trainee.username,
        total_calls=len(calls),
        completed_calls=len(completed),
        average_duration_ms=sum(durations) / len(durations) if durations else None,
        scenarios_attempted=len(scenario_ids),
    )


@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get system health overview (admin only). PRD FR-6.6."""
    active_result = await db.execute(
        select(func.count()).select_from(CallSession).where(CallSession.status == CallSessionStatus.ACTIVE)
    )
    total_result = await db.execute(select(func.count()).select_from(CallSession))
    scenario_result = await db.execute(select(func.count()).select_from(TrainingScenario))
    user_result = await db.execute(select(func.count()).select_from(User))

    return SystemHealthResponse(
        active_calls=active_result.scalar() or 0,
        total_calls=total_result.scalar() or 0,
        total_scenarios=scenario_result.scalar() or 0,
        total_users=user_result.scalar() or 0,
    )


@router.post("/calls/{call_id}/comments")
async def add_call_comment(
    call_id: UUID,
    body: CallReviewComment,
    user: User = Depends(require_role(UserRole.SUPERVISOR, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Add a supervisor comment to a call (PRD FR-6.3)."""
    result = await db.execute(select(CallSession).where(CallSession.id == call_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Call not found")

    metadata = session.session_metadata or {}
    comments = metadata.get("supervisor_comments", [])
    comments.append({
        "author_id": str(user.id),
        "author_username": user.username,
        "comment": body.comment,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    metadata["supervisor_comments"] = comments

    from sqlalchemy import update
    stmt = update(CallSession).where(CallSession.id == call_id).values(session_metadata=metadata)
    await db.execute(stmt)
    await db.commit()

    return {"status": "ok", "comment_count": len(comments)}
