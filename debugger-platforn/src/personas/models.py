"""
Pydantic models for the Persona Builder system.
Defines persona traits, style, edge behaviors, and the persona library.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PersonaTraits(BaseModel):
    patience: int = Field(ge=1, le=10, description="1=very impatient, 10=endlessly patient")
    clarity: int = Field(ge=1, le=10, description="1=very vague, 10=crystal clear")
    tech_savviness: int = Field(ge=1, le=10, description="1=technophobe, 10=expert")
    politeness: int = Field(ge=1, le=10, description="1=rude, 10=extremely polite")
    verbosity: int = Field(ge=1, le=10, description="1=terse, 10=very wordy")


class PersonaStyle(BaseModel):
    tone: str = Field(description="polite|neutral|frustrated|angry")
    formality: str = Field(description="formal|casual|slang")
    typo_rate: float = Field(ge=0.0, le=1.0, description="0.0=perfect typing, 1.0=constant typos")
    abbreviation_use: str = Field(default="low", description="low|medium|high")
    emoji_use: str = Field(default="none", description="none|rare|moderate|frequent")


class PersonaEdgeBehaviors(BaseModel):
    rage_quits: bool = False
    changes_mind: bool = False
    provides_incomplete_info: bool = False
    asks_off_topic: bool = False
    tests_boundaries: bool = False


class Persona(BaseModel):
    persona_id: str
    name: str
    agent_type: str  # support|sales|scheduling|etc
    source: str  # template|ai_generated|custom
    traits: PersonaTraits
    style: PersonaStyle
    edge_behaviors: PersonaEdgeBehaviors
    sample_messages: List[str] = []
    created_at: datetime


class PersonaLibrary(BaseModel):
    persona_library_id: str
    agent_id: str
    personas: List[Persona]
    created_at: datetime
