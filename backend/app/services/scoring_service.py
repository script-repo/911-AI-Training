"""Scoring service for evaluating trainee performance against scenario rubrics"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.protocol_event import CallScore, ProtocolEvent, ProtocolEventType

logger = logging.getLogger(__name__)


# Default scoring rubric if scenario doesn't define one
DEFAULT_RUBRIC = {
    "location_obtained": {"points": 20, "threshold_seconds": 30},
    "callback_number_obtained": {"points": 10, "threshold_seconds": 60},
    "chief_complaint_identified": {"points": 15},
    "consciousness_verified": {"points": 15},
    "breathing_verified": {"points": 15},
    "call_control": {"points": 25},
}


class ScoringService:
    """Computes objective call scores based on protocol events and scenario rubrics."""

    async def compute_score(
        self,
        call_id: UUID,
        duration_ms: int,
        rubric: Optional[Dict[str, Any]] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Compute the final score for a call session.

        Args:
            call_id: The call session ID
            duration_ms: Total call duration in milliseconds
            rubric: Scenario-specific scoring rubric (uses default if None)
            db: Database session for fetching protocol events

        Returns:
            Dict with total_score, subscores, protocol_errors, and feedback
        """
        scoring_rubric = rubric or DEFAULT_RUBRIC

        # Fetch protocol events for this call
        events: List[ProtocolEvent] = []
        if db:
            result = await db.execute(
                select(ProtocolEvent)
                .where(ProtocolEvent.call_id == call_id)
                .order_by(ProtocolEvent.timestamp_ms)
            )
            events = list(result.scalars().all())

        # Build event lookup
        event_map: Dict[str, ProtocolEvent] = {}
        for event in events:
            if event.event_type.value not in event_map:
                event_map[event.event_type.value] = event

        # Score each criterion
        subscores: Dict[str, Dict[str, Any]] = {}
        total_earned = 0.0
        total_possible = 0.0
        protocol_errors: List[Dict[str, Any]] = []
        feedback: List[Dict[str, str]] = []

        for criterion, config in scoring_rubric.items():
            max_points = config.get("points", 0)
            total_possible += max_points
            threshold_seconds = config.get("threshold_seconds")

            event = event_map.get(criterion)

            if event:
                if threshold_seconds:
                    time_seconds = event.timestamp_ms / 1000.0
                    if time_seconds <= threshold_seconds:
                        earned = max_points
                        feedback.append({
                            "criterion": criterion,
                            "message": f"{criterion.replace('_', ' ').title()} obtained at {time_seconds:.1f}s (target < {threshold_seconds}s) - Good!",
                            "rating": "good",
                        })
                    else:
                        # Partial credit - linearly decrease beyond threshold
                        overage_ratio = min((time_seconds - threshold_seconds) / threshold_seconds, 1.0)
                        earned = max_points * (1.0 - overage_ratio * 0.5)
                        protocol_errors.append({
                            "criterion": criterion,
                            "issue": f"Obtained at {time_seconds:.1f}s, target was < {threshold_seconds}s",
                        })
                        feedback.append({
                            "criterion": criterion,
                            "message": f"{criterion.replace('_', ' ').title()} obtained at {time_seconds:.1f}s - target is < {threshold_seconds}s",
                            "rating": "needs_improvement",
                        })
                else:
                    earned = max_points
                    feedback.append({
                        "criterion": criterion,
                        "message": f"{criterion.replace('_', ' ').title()} - Completed",
                        "rating": "good",
                    })
            else:
                earned = 0
                protocol_errors.append({
                    "criterion": criterion,
                    "issue": "Not completed during call",
                })
                feedback.append({
                    "criterion": criterion,
                    "message": f"{criterion.replace('_', ' ').title()} - Missing! This is a required protocol step.",
                    "rating": "missed",
                })

            subscores[criterion] = {
                "points": round(earned, 1),
                "max": max_points,
                "threshold_met": event is not None and (not threshold_seconds or event.timestamp_ms / 1000.0 <= threshold_seconds),
                "time_seconds": event.timestamp_ms / 1000.0 if event else None,
            }
            total_earned += earned

        # Call control score (based on duration and overall handling)
        if "call_control" in scoring_rubric and "call_control" not in subscores:
            cc_points = scoring_rubric["call_control"]["points"]
            total_possible += cc_points
            # Simple heuristic: full points if call completed within reasonable time
            earned = cc_points if duration_ms > 0 else 0
            subscores["call_control"] = {"points": earned, "max": cc_points}
            total_earned += earned

        return {
            "total_score": round(total_earned, 1),
            "max_possible_score": total_possible,
            "subscores": subscores,
            "protocol_errors": protocol_errors,
            "feedback": feedback,
        }

    async def save_score(
        self,
        call_id: UUID,
        score_data: Dict[str, Any],
        db: AsyncSession,
    ) -> CallScore:
        """Persist computed score to database."""
        score = CallScore(
            call_id=call_id,
            total_score=score_data["total_score"],
            max_possible_score=score_data["max_possible_score"],
            subscores=score_data["subscores"],
            protocol_errors=score_data.get("protocol_errors"),
            feedback=score_data.get("feedback"),
        )
        db.add(score)
        await db.commit()
        await db.refresh(score)
        logger.info(f"Score saved for call {call_id}: {score.total_score}/{score.max_possible_score}")
        return score


scoring_service = ScoringService()
