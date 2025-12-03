"""
Database utility functions for development and testing.

Provides helper functions for database operations including:
- Connection testing
- Table creation
- Database seeding
- Database reset
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal, engine
from app.models.database import (
    Base,
    CallSession,
    CallSessionStatus,
    DifficultyLevel,
    TrainingScenario,
)

logger = logging.getLogger(__name__)


async def check_database_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def create_tables() -> None:
    """
    Create all database tables.

    This is useful for development. In production, use Alembic migrations.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


async def drop_tables() -> None:
    """
    Drop all database tables.

    WARNING: This deletes all data! Use only in development/testing.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise


async def seed_training_scenarios(session: Optional[AsyncSession] = None) -> None:
    """
    Seed the database with sample training scenarios.

    Args:
        session: Optional database session. If None, creates a new session.
    """
    should_close = session is None
    if session is None:
        session = AsyncSessionLocal()

    try:
        scenarios = [
            TrainingScenario(
                name="Domestic Violence Call",
                description="A frightened caller reports ongoing domestic violence situation with potential weapon involved.",
                difficulty_level=DifficultyLevel.MEDIUM,
                caller_profile={
                    "emotional_state": "fearful",
                    "background": "Female, mid-30s, lives with abusive partner",
                    "personality": "Hesitant to provide details, afraid of being overheard",
                    "communication_style": "Whispering, speaking in fragments, easily startled"
                },
                scenario_script={
                    "initial_state": {
                        "caller_location": "Locked in bathroom",
                        "threat_level": "High - partner is intoxicated and has threatened violence",
                        "time_of_day": "Late evening",
                        "background_noise": "Occasional shouting, door banging"
                    },
                    "key_entities": [
                        {"type": "LOCATION", "value": "123 Oak Street, Apartment 4B"},
                        {"type": "PERSON", "value": "John (partner)"},
                        {"type": "WEAPON", "value": "Baseball bat"},
                        {"type": "INJURY", "value": "Bruising on arms from earlier"}
                    ],
                    "expected_flow": [
                        "Caller whispers for help",
                        "Operator should speak calmly and quietly",
                        "Extract location information carefully",
                        "Assess immediate danger",
                        "Keep caller on line until help arrives",
                        "Provide safety instructions (stay locked in safe room)"
                    ]
                },
                is_active=True
            ),
            TrainingScenario(
                name="Medical Emergency - Heart Attack",
                description="Panicked caller reporting family member having chest pain and difficulty breathing.",
                difficulty_level=DifficultyLevel.HARD,
                caller_profile={
                    "emotional_state": "panicked",
                    "background": "Adult son calling about elderly father",
                    "personality": "Frantic, talking rapidly, struggling to follow instructions",
                    "communication_style": "Speaking loudly and quickly, interrupting with updates"
                },
                scenario_script={
                    "initial_state": {
                        "caller_location": "Home residence",
                        "threat_level": "Critical - potential cardiac arrest",
                        "time_of_day": "Morning",
                        "background_noise": "Groaning, labored breathing"
                    },
                    "key_entities": [
                        {"type": "LOCATION", "value": "456 Maple Drive"},
                        {"type": "PERSON", "value": "Father, age 67"},
                        {"type": "INJURY", "value": "Severe chest pain, shortness of breath, sweating"},
                        {"type": "TIME_REFERENCE", "value": "Symptoms started 10 minutes ago"}
                    ],
                    "expected_flow": [
                        "Caller frantically describes symptoms",
                        "Operator must remain calm and assertive",
                        "Get exact location and callback number",
                        "Assess consciousness and breathing",
                        "Provide CPR instructions if needed",
                        "Guide caller to give aspirin if available",
                        "Keep caller calm and prepared for paramedics"
                    ]
                },
                is_active=True
            ),
            TrainingScenario(
                name="Car Accident - Minor Injuries",
                description="Witness reporting a two-car collision with minor injuries at an intersection.",
                difficulty_level=DifficultyLevel.EASY,
                caller_profile={
                    "emotional_state": "calm",
                    "background": "Bystander who witnessed the accident",
                    "personality": "Helpful, observant, able to provide clear details",
                    "communication_style": "Speaking clearly, willing to stay and help"
                },
                scenario_script={
                    "initial_state": {
                        "caller_location": "At the scene as witness",
                        "threat_level": "Low - minor injuries, no fire",
                        "time_of_day": "Afternoon",
                        "background_noise": "Traffic sounds, people talking"
                    },
                    "key_entities": [
                        {"type": "LOCATION", "value": "Intersection of Main St and 5th Ave"},
                        {"type": "VEHICLE", "value": "Red sedan and blue pickup truck"},
                        {"type": "INJURY", "value": "One driver has cut on forehead"},
                        {"type": "PERSON", "value": "Two drivers involved"}
                    ],
                    "expected_flow": [
                        "Caller calmly reports accident",
                        "Operator gets location and number of vehicles",
                        "Assess injuries and hazards",
                        "Determine if anyone is trapped",
                        "Ask about fuel leaks or fire",
                        "Keep caller to direct emergency vehicles if needed"
                    ]
                },
                is_active=True
            ),
            TrainingScenario(
                name="Active Shooter Report",
                description="Multiple callers reporting gunshots and active shooter at a school.",
                difficulty_level=DifficultyLevel.HARD,
                caller_profile={
                    "emotional_state": "hysterical",
                    "background": "Teacher hiding in classroom with students",
                    "personality": "Terrified, trying to stay quiet while reporting",
                    "communication_style": "Whispered, fragmented sentences, crying"
                },
                scenario_script={
                    "initial_state": {
                        "caller_location": "Classroom, barricaded inside",
                        "threat_level": "Critical - active shooter situation",
                        "time_of_day": "School hours",
                        "background_noise": "Distant gunshots, screaming, running footsteps"
                    },
                    "key_entities": [
                        {"type": "LOCATION", "value": "Roosevelt High School, Building C, Room 204"},
                        {"type": "WEAPON", "value": "Gunshots heard"},
                        {"type": "PERSON", "value": "Unknown shooter, approximately 15 students in room"},
                        {"type": "INJURY", "value": "Unknown casualties"}
                    ],
                    "expected_flow": [
                        "Caller reports shots fired",
                        "Operator must remain extremely calm and authoritative",
                        "Get precise location within building",
                        "Determine if caller is safe/hidden",
                        "Instruct to stay quiet and hidden",
                        "Get description of shooter if available",
                        "Keep line open but silent if necessary",
                        "Coordinate with multiple agencies"
                    ]
                },
                is_active=True
            ),
            TrainingScenario(
                name="Burglary in Progress",
                description="Homeowner reports hearing someone breaking into their house while they hide upstairs.",
                difficulty_level=DifficultyLevel.MEDIUM,
                caller_profile={
                    "emotional_state": "anxious",
                    "background": "Homeowner alone, awakened by breaking glass",
                    "personality": "Scared but trying to stay composed",
                    "communication_style": "Whispering urgently, asking for immediate help"
                },
                scenario_script={
                    "initial_state": {
                        "caller_location": "Upstairs bedroom, door locked",
                        "threat_level": "High - intruder in home",
                        "time_of_day": "Late night, 2 AM",
                        "background_noise": "Glass breaking, footsteps downstairs, items being moved"
                    },
                    "key_entities": [
                        {"type": "LOCATION", "value": "789 Pine Street"},
                        {"type": "PERSON", "value": "Unknown number of intruders"},
                        {"type": "TIME_REFERENCE", "value": "Breaking in now"},
                        {"type": "WEAPON", "value": "Unknown if armed"}
                    ],
                    "expected_flow": [
                        "Caller whispers about break-in",
                        "Operator speaks softly and calmly",
                        "Get address and confirm caller is safe",
                        "Determine caller's exact location in house",
                        "Advise to stay quiet and hidden",
                        "Ask about weapons in home (for officer safety)",
                        "Get description of sounds/movements",
                        "Keep caller on line until police arrive",
                        "Advise when officers are on scene"
                    ]
                },
                is_active=True
            )
        ]

        for scenario in scenarios:
            session.add(scenario)

        await session.commit()
        logger.info(f"Successfully seeded {len(scenarios)} training scenarios")

    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to seed training scenarios: {e}")
        raise
    finally:
        if should_close:
            await session.close()


async def reset_database() -> None:
    """
    Reset the database by dropping and recreating all tables, then seeding with sample data.

    WARNING: This deletes all data! Use only in development/testing.
    """
    logger.warning("Resetting database - all data will be lost!")

    # Drop all tables
    await drop_tables()

    # Create all tables
    await create_tables()

    # Seed with training scenarios
    await seed_training_scenarios()

    logger.info("Database reset complete")


async def get_database_info() -> dict:
    """
    Get information about the database state.

    Returns:
        dict: Database information including table counts
    """
    async with AsyncSessionLocal() as session:
        try:
            # Get counts for each table
            from sqlalchemy import select, func

            scenario_count = await session.scalar(
                select(func.count()).select_from(TrainingScenario)
            )
            session_count = await session.scalar(
                select(func.count()).select_from(CallSession)
            )

            return {
                "connection": "OK",
                "scenarios": scenario_count or 0,
                "sessions": session_count or 0,
            }
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {
                "connection": "FAILED",
                "error": str(e)
            }


# CLI utility for running these functions
if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("Usage: python -m app.db.utils [check|create|drop|seed|reset|info]")
            return

        command = sys.argv[1]

        if command == "check":
            success = await check_database_connection()
            print(f"Connection: {'OK' if success else 'FAILED'}")
        elif command == "create":
            await create_tables()
            print("Tables created")
        elif command == "drop":
            await drop_tables()
            print("Tables dropped")
        elif command == "seed":
            await seed_training_scenarios()
            print("Database seeded")
        elif command == "reset":
            await reset_database()
            print("Database reset")
        elif command == "info":
            info = await get_database_info()
            print("Database Info:")
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            print(f"Unknown command: {command}")

    asyncio.run(main())
