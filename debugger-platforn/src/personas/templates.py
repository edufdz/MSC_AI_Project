"""
Pre-built persona templates organized by agent domain.
Each template provides default traits, style, and edge behaviors.
"""

from __future__ import annotations

from typing import Dict, List

PERSONA_TEMPLATES: Dict[str, List[Dict]] = {
    "support": [
        {
            "name": "Frustrated Customer",
            "traits": {
                "patience": 2, "clarity": 4, "tech_savviness": 3,
                "politeness": 3, "verbosity": 5,
            },
            "style": {
                "tone": "frustrated", "formality": "casual",
                "typo_rate": 0.15, "abbreviation_use": "high", "emoji_use": "rare",
            },
            "edge_behaviors": {
                "rage_quits": True, "changes_mind": False,
                "provides_incomplete_info": False, "asks_off_topic": False,
                "tests_boundaries": False,
            },
        },
        {
            "name": "Confused First-Timer",
            "traits": {
                "patience": 6, "clarity": 3, "tech_savviness": 2,
                "politeness": 8, "verbosity": 8,
            },
            "style": {
                "tone": "neutral", "formality": "casual",
                "typo_rate": 0.10, "abbreviation_use": "low", "emoji_use": "rare",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": False,
                "provides_incomplete_info": True, "asks_off_topic": False,
                "tests_boundaries": False,
            },
        },
        {
            "name": "Power User",
            "traits": {
                "patience": 7, "clarity": 9, "tech_savviness": 9,
                "politeness": 6, "verbosity": 5,
            },
            "style": {
                "tone": "neutral", "formality": "formal",
                "typo_rate": 0.02, "abbreviation_use": "low", "emoji_use": "none",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": False,
                "provides_incomplete_info": False, "asks_off_topic": False,
                "tests_boundaries": True,
            },
        },
        {
            "name": "Angry Escalator",
            "traits": {
                "patience": 1, "clarity": 6, "tech_savviness": 5,
                "politeness": 1, "verbosity": 7,
            },
            "style": {
                "tone": "angry", "formality": "casual",
                "typo_rate": 0.20, "abbreviation_use": "medium", "emoji_use": "none",
            },
            "edge_behaviors": {
                "rage_quits": True, "changes_mind": False,
                "provides_incomplete_info": False, "asks_off_topic": True,
                "tests_boundaries": True,
            },
        },
        {
            "name": "Polite Elderly User",
            "traits": {
                "patience": 9, "clarity": 5, "tech_savviness": 2,
                "politeness": 10, "verbosity": 9,
            },
            "style": {
                "tone": "polite", "formality": "formal",
                "typo_rate": 0.08, "abbreviation_use": "low", "emoji_use": "none",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": False,
                "provides_incomplete_info": True, "asks_off_topic": True,
                "tests_boundaries": False,
            },
        },
    ],

    "sales": [
        {
            "name": "Budget-Conscious Researcher",
            "traits": {
                "patience": 8, "clarity": 7, "tech_savviness": 6,
                "politeness": 7, "verbosity": 4,
            },
            "style": {
                "tone": "neutral", "formality": "casual",
                "typo_rate": 0.05, "abbreviation_use": "low", "emoji_use": "none",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": True,
                "provides_incomplete_info": False, "asks_off_topic": False,
                "tests_boundaries": False,
            },
        },
        {
            "name": "Impulsive Buyer",
            "traits": {
                "patience": 3, "clarity": 5, "tech_savviness": 4,
                "politeness": 5, "verbosity": 3,
            },
            "style": {
                "tone": "neutral", "formality": "casual",
                "typo_rate": 0.12, "abbreviation_use": "high", "emoji_use": "moderate",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": False,
                "provides_incomplete_info": True, "asks_off_topic": False,
                "tests_boundaries": False,
            },
        },
        {
            "name": "Skeptical Evaluator",
            "traits": {
                "patience": 6, "clarity": 8, "tech_savviness": 8,
                "politeness": 5, "verbosity": 6,
            },
            "style": {
                "tone": "neutral", "formality": "formal",
                "typo_rate": 0.02, "abbreviation_use": "low", "emoji_use": "none",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": True,
                "provides_incomplete_info": False, "asks_off_topic": False,
                "tests_boundaries": True,
            },
        },
    ],

    "scheduling": [
        {
            "name": "Last-Minute Booker",
            "traits": {
                "patience": 3, "clarity": 5, "tech_savviness": 5,
                "politeness": 4, "verbosity": 4,
            },
            "style": {
                "tone": "frustrated", "formality": "casual",
                "typo_rate": 0.15, "abbreviation_use": "high", "emoji_use": "moderate",
            },
            "edge_behaviors": {
                "rage_quits": True, "changes_mind": True,
                "provides_incomplete_info": False, "asks_off_topic": False,
                "tests_boundaries": False,
            },
        },
        {
            "name": "Meticulous Planner",
            "traits": {
                "patience": 9, "clarity": 8, "tech_savviness": 6,
                "politeness": 8, "verbosity": 8,
            },
            "style": {
                "tone": "polite", "formality": "formal",
                "typo_rate": 0.03, "abbreviation_use": "low", "emoji_use": "none",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": True,
                "provides_incomplete_info": False, "asks_off_topic": False,
                "tests_boundaries": False,
            },
        },
        {
            "name": "Group Coordinator",
            "traits": {
                "patience": 5, "clarity": 6, "tech_savviness": 5,
                "politeness": 7, "verbosity": 7,
            },
            "style": {
                "tone": "neutral", "formality": "casual",
                "typo_rate": 0.08, "abbreviation_use": "medium", "emoji_use": "rare",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": True,
                "provides_incomplete_info": True, "asks_off_topic": True,
                "tests_boundaries": False,
            },
        },
    ],

    "research": [
        {
            "name": "Focused Analyst",
            "traits": {
                "patience": 8, "clarity": 9, "tech_savviness": 8,
                "politeness": 7, "verbosity": 6,
            },
            "style": {
                "tone": "neutral", "formality": "formal",
                "typo_rate": 0.02, "abbreviation_use": "low", "emoji_use": "none",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": False,
                "provides_incomplete_info": False, "asks_off_topic": False,
                "tests_boundaries": True,
            },
        },
        {
            "name": "Exploratory Thinker",
            "traits": {
                "patience": 7, "clarity": 5, "tech_savviness": 6,
                "politeness": 7, "verbosity": 8,
            },
            "style": {
                "tone": "polite", "formality": "casual",
                "typo_rate": 0.05, "abbreviation_use": "low", "emoji_use": "rare",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": True,
                "provides_incomplete_info": True, "asks_off_topic": True,
                "tests_boundaries": False,
            },
        },
    ],

    "coding": [
        {
            "name": "Junior Developer",
            "traits": {
                "patience": 6, "clarity": 4, "tech_savviness": 5,
                "politeness": 7, "verbosity": 7,
            },
            "style": {
                "tone": "neutral", "formality": "casual",
                "typo_rate": 0.08, "abbreviation_use": "medium", "emoji_use": "rare",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": True,
                "provides_incomplete_info": True, "asks_off_topic": True,
                "tests_boundaries": False,
            },
        },
        {
            "name": "Senior Engineer",
            "traits": {
                "patience": 5, "clarity": 9, "tech_savviness": 10,
                "politeness": 5, "verbosity": 3,
            },
            "style": {
                "tone": "neutral", "formality": "casual",
                "typo_rate": 0.01, "abbreviation_use": "medium", "emoji_use": "none",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": False,
                "provides_incomplete_info": False, "asks_off_topic": False,
                "tests_boundaries": True,
            },
        },
    ],
}

# Fallback: generic personas usable for any agent type
GENERIC_PERSONAS: List[Dict] = [
    {
        "name": "Happy Path User",
        "traits": {
            "patience": 8, "clarity": 8, "tech_savviness": 6,
            "politeness": 8, "verbosity": 5,
        },
        "style": {
            "tone": "polite", "formality": "casual",
            "typo_rate": 0.03, "abbreviation_use": "low", "emoji_use": "rare",
        },
        "edge_behaviors": {
            "rage_quits": False, "changes_mind": False,
            "provides_incomplete_info": False, "asks_off_topic": False,
            "tests_boundaries": False,
        },
    },
    {
        "name": "Edge-Case Explorer",
        "traits": {
            "patience": 6, "clarity": 7, "tech_savviness": 8,
            "politeness": 5, "verbosity": 5,
        },
        "style": {
            "tone": "neutral", "formality": "casual",
            "typo_rate": 0.05, "abbreviation_use": "medium", "emoji_use": "none",
        },
        "edge_behaviors": {
            "rage_quits": False, "changes_mind": True,
            "provides_incomplete_info": True, "asks_off_topic": True,
            "tests_boundaries": True,
        },
    },
    {
        "name": "Adversarial Tester",
        "traits": {
            "patience": 4, "clarity": 6, "tech_savviness": 9,
            "politeness": 2, "verbosity": 4,
        },
        "style": {
            "tone": "angry", "formality": "slang",
            "typo_rate": 0.10, "abbreviation_use": "high", "emoji_use": "none",
        },
        "edge_behaviors": {
            "rage_quits": True, "changes_mind": True,
            "provides_incomplete_info": True, "asks_off_topic": True,
            "tests_boundaries": True,
        },
    },
]


def load_persona_templates(agent_type: str) -> List[Dict]:
    """
    Load pre-built persona templates for an agent type.
    Falls back to generic personas if the type isn't recognised.
    """
    templates = PERSONA_TEMPLATES.get(agent_type, [])
    if not templates:
        templates = GENERIC_PERSONAS
    return templates
