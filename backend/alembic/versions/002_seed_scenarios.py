"""Seed training scenarios for 911 Operator Training Simulator

Revision ID: 002
Revises: 001
Create Date: 2025-12-03

This migration seeds the database with realistic training scenarios covering
various emergency types and difficulty levels:
- Domestic Violence Call (medium)
- Medical Emergency - Heart Attack (hard)
- Car Accident - Minor Injuries (easy)
- Active Shooter Report (hard)
- Burglary in Progress (medium)

Each scenario includes:
- Realistic caller profile with emotional state
- Detailed scenario script with key entities
- Expected dialogue flow for training evaluation
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert seed training scenarios."""

    # Create table reference for bulk insert
    training_scenarios = sa.table(
        'training_scenarios',
        sa.column('id', postgresql.UUID(as_uuid=True)),
        sa.column('name', sa.String(200)),
        sa.column('description', sa.Text()),
        sa.column('caller_profile', postgresql.JSONB()),
        sa.column('scenario_script', postgresql.JSONB()),
        sa.column('difficulty_level', sa.String(20)),
        sa.column('is_active', sa.Boolean()),
    )

    scenarios = [
        {
            'id': uuid.uuid4(),
            'name': 'Domestic Violence Call',
            'description': 'A frightened caller reports ongoing domestic violence situation with potential weapon involved.',
            'difficulty_level': 'medium',
            'is_active': True,
            'caller_profile': {
                'emotional_state': 'fearful',
                'background': 'Female, mid-30s, lives with abusive partner',
                'personality': 'Hesitant to provide details, afraid of being overheard',
                'communication_style': 'Whispering, speaking in fragments, easily startled'
            },
            'scenario_script': {
                'initial_state': {
                    'caller_location': 'Locked in bathroom',
                    'threat_level': 'High - partner is intoxicated and has threatened violence',
                    'time_of_day': 'Late evening',
                    'background_noise': 'Occasional shouting, door banging'
                },
                'key_entities': [
                    {'type': 'LOCATION', 'value': '123 Oak Street, Apartment 4B'},
                    {'type': 'PERSON', 'value': 'John (partner)'},
                    {'type': 'WEAPON', 'value': 'Baseball bat'},
                    {'type': 'INJURY', 'value': 'Bruising on arms from earlier'}
                ],
                'expected_flow': [
                    'Caller whispers for help',
                    'Operator should speak calmly and quietly',
                    'Extract location information carefully',
                    'Assess immediate danger',
                    'Keep caller on line until help arrives',
                    'Provide safety instructions (stay locked in safe room)'
                ]
            }
        },
        {
            'id': uuid.uuid4(),
            'name': 'Medical Emergency - Heart Attack',
            'description': 'Panicked caller reporting family member having chest pain and difficulty breathing.',
            'difficulty_level': 'hard',
            'is_active': True,
            'caller_profile': {
                'emotional_state': 'panicked',
                'background': 'Adult son calling about elderly father',
                'personality': 'Frantic, talking rapidly, struggling to follow instructions',
                'communication_style': 'Speaking loudly and quickly, interrupting with updates'
            },
            'scenario_script': {
                'initial_state': {
                    'caller_location': 'Home residence',
                    'threat_level': 'Critical - potential cardiac arrest',
                    'time_of_day': 'Morning',
                    'background_noise': 'Groaning, labored breathing'
                },
                'key_entities': [
                    {'type': 'LOCATION', 'value': '456 Maple Drive'},
                    {'type': 'PERSON', 'value': 'Father, age 67'},
                    {'type': 'INJURY', 'value': 'Severe chest pain, shortness of breath, sweating'},
                    {'type': 'TIME_REFERENCE', 'value': 'Symptoms started 10 minutes ago'}
                ],
                'expected_flow': [
                    'Caller frantically describes symptoms',
                    'Operator must remain calm and assertive',
                    'Get exact location and callback number',
                    'Assess consciousness and breathing',
                    'Provide CPR instructions if needed',
                    'Guide caller to give aspirin if available',
                    'Keep caller calm and prepared for paramedics'
                ]
            }
        },
        {
            'id': uuid.uuid4(),
            'name': 'Car Accident - Minor Injuries',
            'description': 'Witness reporting a two-car collision with minor injuries at an intersection.',
            'difficulty_level': 'easy',
            'is_active': True,
            'caller_profile': {
                'emotional_state': 'calm',
                'background': 'Bystander who witnessed the accident',
                'personality': 'Helpful, observant, able to provide clear details',
                'communication_style': 'Speaking clearly, willing to stay and help'
            },
            'scenario_script': {
                'initial_state': {
                    'caller_location': 'At the scene as witness',
                    'threat_level': 'Low - minor injuries, no fire',
                    'time_of_day': 'Afternoon',
                    'background_noise': 'Traffic sounds, people talking'
                },
                'key_entities': [
                    {'type': 'LOCATION', 'value': 'Intersection of Main St and 5th Ave'},
                    {'type': 'VEHICLE', 'value': 'Red sedan and blue pickup truck'},
                    {'type': 'INJURY', 'value': 'One driver has cut on forehead'},
                    {'type': 'PERSON', 'value': 'Two drivers involved'}
                ],
                'expected_flow': [
                    'Caller calmly reports accident',
                    'Operator gets location and number of vehicles',
                    'Assess injuries and hazards',
                    'Determine if anyone is trapped',
                    'Ask about fuel leaks or fire',
                    'Keep caller to direct emergency vehicles if needed'
                ]
            }
        },
        {
            'id': uuid.uuid4(),
            'name': 'Active Shooter Report',
            'description': 'Multiple callers reporting gunshots and active shooter at a school.',
            'difficulty_level': 'hard',
            'is_active': True,
            'caller_profile': {
                'emotional_state': 'hysterical',
                'background': 'Teacher hiding in classroom with students',
                'personality': 'Terrified, trying to stay quiet while reporting',
                'communication_style': 'Whispered, fragmented sentences, crying'
            },
            'scenario_script': {
                'initial_state': {
                    'caller_location': 'Classroom, barricaded inside',
                    'threat_level': 'Critical - active shooter situation',
                    'time_of_day': 'School hours',
                    'background_noise': 'Distant gunshots, screaming, running footsteps'
                },
                'key_entities': [
                    {'type': 'LOCATION', 'value': 'Roosevelt High School, Building C, Room 204'},
                    {'type': 'WEAPON', 'value': 'Gunshots heard'},
                    {'type': 'PERSON', 'value': 'Unknown shooter, approximately 15 students in room'},
                    {'type': 'INJURY', 'value': 'Unknown casualties'}
                ],
                'expected_flow': [
                    'Caller reports shots fired',
                    'Operator must remain extremely calm and authoritative',
                    'Get precise location within building',
                    'Determine if caller is safe/hidden',
                    'Instruct to stay quiet and hidden',
                    'Get description of shooter if available',
                    'Keep line open but silent if necessary',
                    'Coordinate with multiple agencies'
                ]
            }
        },
        {
            'id': uuid.uuid4(),
            'name': 'Burglary in Progress',
            'description': 'Homeowner reports hearing someone breaking into their house while they hide upstairs.',
            'difficulty_level': 'medium',
            'is_active': True,
            'caller_profile': {
                'emotional_state': 'anxious',
                'background': 'Homeowner alone, awakened by breaking glass',
                'personality': 'Scared but trying to stay composed',
                'communication_style': 'Whispering urgently, asking for immediate help'
            },
            'scenario_script': {
                'initial_state': {
                    'caller_location': 'Upstairs bedroom, door locked',
                    'threat_level': 'High - intruder in home',
                    'time_of_day': 'Late night, 2 AM',
                    'background_noise': 'Glass breaking, footsteps downstairs, items being moved'
                },
                'key_entities': [
                    {'type': 'LOCATION', 'value': '789 Pine Street'},
                    {'type': 'PERSON', 'value': 'Unknown number of intruders'},
                    {'type': 'TIME_REFERENCE', 'value': 'Breaking in now'},
                    {'type': 'WEAPON', 'value': 'Unknown if armed'}
                ],
                'expected_flow': [
                    'Caller whispers about break-in',
                    'Operator speaks softly and calmly',
                    'Get address and confirm caller is safe',
                    'Determine caller\'s exact location in house',
                    'Advise to stay quiet and hidden',
                    'Ask about weapons in home (for officer safety)',
                    'Get description of sounds/movements',
                    'Keep caller on line until police arrive',
                    'Advise when officers are on scene'
                ]
            }
        }
    ]

    # Insert all scenarios
    op.bulk_insert(training_scenarios, scenarios)


def downgrade() -> None:
    """Remove seed training scenarios."""

    # Delete all scenarios (you could be more selective if needed)
    op.execute("""
        DELETE FROM training_scenarios
        WHERE name IN (
            'Domestic Violence Call',
            'Medical Emergency - Heart Attack',
            'Car Accident - Minor Injuries',
            'Active Shooter Report',
            'Burglary in Progress'
        )
    """)
