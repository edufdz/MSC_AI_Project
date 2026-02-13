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
                "emotional_volatility": 8, "trust_level": 3,
                "detail_orientation": 4, "decision_speed": 7,
                "language_proficiency": 7,
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
                "emotional_volatility": 4, "trust_level": 7,
                "detail_orientation": 3, "decision_speed": 3,
                "language_proficiency": 8,
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
                "emotional_volatility": 3, "trust_level": 4,
                "detail_orientation": 8, "decision_speed": 7,
                "language_proficiency": 9,
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
                "emotional_volatility": 10, "trust_level": 2,
                "detail_orientation": 5, "decision_speed": 8,
                "language_proficiency": 7,
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
                "emotional_volatility": 2, "trust_level": 8,
                "detail_orientation": 4, "decision_speed": 3,
                "language_proficiency": 9,
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
        # ── New support personas ──
        {
            "name": "Non-Native Speaker",
            "traits": {
                "patience": 7, "clarity": 4, "tech_savviness": 5,
                "politeness": 7, "verbosity": 6,
                "emotional_volatility": 5, "trust_level": 6,
                "detail_orientation": 5, "decision_speed": 4,
                "language_proficiency": 3,
            },
            "style": {
                "tone": "neutral", "formality": "casual",
                "typo_rate": 0.18, "abbreviation_use": "low", "emoji_use": "rare",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": False,
                "provides_incomplete_info": True, "asks_off_topic": False,
                "tests_boundaries": False,
            },
        },
        {
            "name": "Accessibility-Focused User",
            "traits": {
                "patience": 7, "clarity": 7, "tech_savviness": 6,
                "politeness": 8, "verbosity": 7,
                "emotional_volatility": 4, "trust_level": 5,
                "detail_orientation": 8, "decision_speed": 5,
                "language_proficiency": 9,
            },
            "style": {
                "tone": "polite", "formality": "formal",
                "typo_rate": 0.05, "abbreviation_use": "low", "emoji_use": "none",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": False,
                "provides_incomplete_info": False, "asks_off_topic": False,
                "tests_boundaries": True,
            },
        },
        {
            "name": "Multi-Tasking Parent",
            "traits": {
                "patience": 4, "clarity": 5, "tech_savviness": 5,
                "politeness": 6, "verbosity": 4,
                "emotional_volatility": 6, "trust_level": 5,
                "detail_orientation": 4, "decision_speed": 8,
                "language_proficiency": 8,
            },
            "style": {
                "tone": "neutral", "formality": "casual",
                "typo_rate": 0.12, "abbreviation_use": "high", "emoji_use": "moderate",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": True,
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
                "emotional_volatility": 3, "trust_level": 4,
                "detail_orientation": 8, "decision_speed": 3,
                "language_proficiency": 8,
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
                "emotional_volatility": 7, "trust_level": 7,
                "detail_orientation": 2, "decision_speed": 10,
                "language_proficiency": 7,
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
                "emotional_volatility": 3, "trust_level": 2,
                "detail_orientation": 9, "decision_speed": 4,
                "language_proficiency": 9,
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
        # ── New sales personas ──
        {
            "name": "Loyalty Program Member",
            "traits": {
                "patience": 7, "clarity": 7, "tech_savviness": 5,
                "politeness": 8, "verbosity": 5,
                "emotional_volatility": 3, "trust_level": 8,
                "detail_orientation": 6, "decision_speed": 6,
                "language_proficiency": 8,
            },
            "style": {
                "tone": "polite", "formality": "casual",
                "typo_rate": 0.04, "abbreviation_use": "low", "emoji_use": "rare",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": False,
                "provides_incomplete_info": False, "asks_off_topic": False,
                "tests_boundaries": True,
            },
        },
        {
            "name": "Comparison Shopper",
            "traits": {
                "patience": 5, "clarity": 8, "tech_savviness": 7,
                "politeness": 5, "verbosity": 7,
                "emotional_volatility": 4, "trust_level": 3,
                "detail_orientation": 9, "decision_speed": 2,
                "language_proficiency": 9,
            },
            "style": {
                "tone": "neutral", "formality": "formal",
                "typo_rate": 0.02, "abbreviation_use": "low", "emoji_use": "none",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": True,
                "provides_incomplete_info": False, "asks_off_topic": True,
                "tests_boundaries": False,
            },
        },
    ],

    "scheduling": [
        {
            "name": "Last-Minute Booker",
            "traits": {
                "patience": 3, "clarity": 5, "tech_savviness": 5,
                "politeness": 4, "verbosity": 4,
                "emotional_volatility": 7, "trust_level": 5,
                "detail_orientation": 3, "decision_speed": 9,
                "language_proficiency": 7,
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
                "emotional_volatility": 2, "trust_level": 6,
                "detail_orientation": 10, "decision_speed": 2,
                "language_proficiency": 9,
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
                "emotional_volatility": 5, "trust_level": 6,
                "detail_orientation": 6, "decision_speed": 4,
                "language_proficiency": 8,
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
        # ── New scheduling personas ──
        {
            "name": "Timezone-Confused Traveler",
            "traits": {
                "patience": 6, "clarity": 3, "tech_savviness": 4,
                "politeness": 6, "verbosity": 6,
                "emotional_volatility": 6, "trust_level": 5,
                "detail_orientation": 4, "decision_speed": 5,
                "language_proficiency": 6,
            },
            "style": {
                "tone": "neutral", "formality": "casual",
                "typo_rate": 0.10, "abbreviation_use": "medium", "emoji_use": "rare",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": True,
                "provides_incomplete_info": True, "asks_off_topic": False,
                "tests_boundaries": False,
            },
        },
        {
            "name": "Corporate Assistant",
            "traits": {
                "patience": 7, "clarity": 8, "tech_savviness": 7,
                "politeness": 8, "verbosity": 3,
                "emotional_volatility": 2, "trust_level": 6,
                "detail_orientation": 8, "decision_speed": 7,
                "language_proficiency": 9,
            },
            "style": {
                "tone": "neutral", "formality": "formal",
                "typo_rate": 0.01, "abbreviation_use": "low", "emoji_use": "none",
            },
            "edge_behaviors": {
                "rage_quits": False, "changes_mind": True,
                "provides_incomplete_info": False, "asks_off_topic": False,
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
                "emotional_volatility": 2, "trust_level": 5,
                "detail_orientation": 9, "decision_speed": 5,
                "language_proficiency": 9,
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
                "emotional_volatility": 4, "trust_level": 6,
                "detail_orientation": 5, "decision_speed": 4,
                "language_proficiency": 8,
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
                "emotional_volatility": 5, "trust_level": 7,
                "detail_orientation": 4, "decision_speed": 4,
                "language_proficiency": 7,
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
                "emotional_volatility": 3, "trust_level": 3,
                "detail_orientation": 9, "decision_speed": 7,
                "language_proficiency": 9,
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
            "emotional_volatility": 2, "trust_level": 8,
            "detail_orientation": 5, "decision_speed": 6,
            "language_proficiency": 9,
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
            "emotional_volatility": 5, "trust_level": 4,
            "detail_orientation": 7, "decision_speed": 5,
            "language_proficiency": 8,
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
            "emotional_volatility": 8, "trust_level": 1,
            "detail_orientation": 7, "decision_speed": 8,
            "language_proficiency": 8,
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
    # ── New generic personas ──
    {
        "name": "Distracted User",
        "traits": {
            "patience": 5, "clarity": 4, "tech_savviness": 5,
            "politeness": 6, "verbosity": 2,
            "emotional_volatility": 4, "trust_level": 5,
            "detail_orientation": 2, "decision_speed": 7,
            "language_proficiency": 7,
        },
        "style": {
            "tone": "neutral", "formality": "casual",
            "typo_rate": 0.15, "abbreviation_use": "high", "emoji_use": "moderate",
        },
        "edge_behaviors": {
            "rage_quits": False, "changes_mind": True,
            "provides_incomplete_info": True, "asks_off_topic": True,
            "tests_boundaries": False,
        },
    },
    {
        "name": "Overthinker",
        "traits": {
            "patience": 8, "clarity": 6, "tech_savviness": 6,
            "politeness": 7, "verbosity": 9,
            "emotional_volatility": 6, "trust_level": 4,
            "detail_orientation": 9, "decision_speed": 2,
            "language_proficiency": 8,
        },
        "style": {
            "tone": "neutral", "formality": "formal",
            "typo_rate": 0.03, "abbreviation_use": "low", "emoji_use": "none",
        },
        "edge_behaviors": {
            "rage_quits": False, "changes_mind": True,
            "provides_incomplete_info": False, "asks_off_topic": True,
            "tests_boundaries": False,
        },
    },
]


# ── Spanish translations ──────────────────────────────────────────
# Only persona names are translated; numeric traits/style/edge_behaviors stay identical.

_ES_NAME_MAP = {
    # support
    "Frustrated Customer": "Cliente Frustrado",
    "Confused First-Timer": "Primerizo Confundido",
    "Power User": "Usuario Experto",
    "Angry Escalator": "Escalador Enojado",
    "Polite Elderly User": "Usuario Mayor Amable",
    "Non-Native Speaker": "Hablante No Nativo",
    "Accessibility-Focused User": "Usuario Enfocado en Accesibilidad",
    "Multi-Tasking Parent": "Padre Multitarea",
    # scheduling
    "Last-Minute Booker": "Reservador de Último Minuto",
    "Meticulous Planner": "Planificador Meticuloso",
    "Group Coordinator": "Coordinador de Grupo",
    "Timezone-Confused Traveler": "Viajero Confundido con Horarios",
    "Corporate Assistant": "Asistente Corporativo",
    # sales
    "Budget-Conscious Researcher": "Investigador Consciente del Presupuesto",
    "Impulsive Buyer": "Comprador Impulsivo",
    "Skeptical Evaluator": "Evaluador Escéptico",
    "Loyalty Program Member": "Miembro del Programa de Lealtad",
    "Comparison Shopper": "Comprador Comparativo",
    # research
    "Focused Analyst": "Analista Enfocado",
    "Exploratory Thinker": "Pensador Exploratorio",
    # coding
    "Junior Developer": "Desarrollador Junior",
    "Senior Engineer": "Ingeniero Senior",
    # generic
    "Happy Path User": "Usuario Camino Feliz",
    "Edge-Case Explorer": "Explorador de Casos Límite",
    "Adversarial Tester": "Probador Adversario",
    "Distracted User": "Usuario Distraído",
    "Overthinker": "Pensador Excesivo",
}


# ── Portuguese translations ──────────────────────────────────────
_PT_NAME_MAP = {
    # support
    "Frustrated Customer": "Cliente Frustrado",
    "Confused First-Timer": "Iniciante Confuso",
    "Power User": "Usuário Avançado",
    "Angry Escalator": "Escalador Irritado",
    "Polite Elderly User": "Usuário Idoso Educado",
    "Non-Native Speaker": "Falante Não Nativo",
    "Accessibility-Focused User": "Usuário Focado em Acessibilidade",
    "Multi-Tasking Parent": "Pai Multitarefa",
    # scheduling
    "Last-Minute Booker": "Reserva de Última Hora",
    "Meticulous Planner": "Planejador Meticuloso",
    "Group Coordinator": "Coordenador de Grupo",
    "Timezone-Confused Traveler": "Viajante Confuso com Fuso Horário",
    "Corporate Assistant": "Assistente Corporativo",
    # sales
    "Budget-Conscious Researcher": "Pesquisador Consciente do Orçamento",
    "Impulsive Buyer": "Comprador Impulsivo",
    "Skeptical Evaluator": "Avaliador Cético",
    "Loyalty Program Member": "Membro do Programa de Fidelidade",
    "Comparison Shopper": "Comprador Comparativo",
    # research
    "Focused Analyst": "Analista Focado",
    "Exploratory Thinker": "Pensador Exploratório",
    # coding
    "Junior Developer": "Desenvolvedor Júnior",
    "Senior Engineer": "Engenheiro Sênior",
    # generic
    "Happy Path User": "Usuário Caminho Feliz",
    "Edge-Case Explorer": "Explorador de Casos Limite",
    "Adversarial Tester": "Testador Adversário",
    "Distracted User": "Usuário Distraído",
    "Overthinker": "Pensador Excessivo",
}


def _translate_personas(templates: List[Dict], name_map: Dict[str, str]) -> List[Dict]:
    """Return a copy of *templates* with names translated using the given map."""
    translated = []
    for tpl in templates:
        t = dict(tpl)
        t["name"] = name_map.get(t["name"], t["name"])
        translated.append(t)
    return translated


PERSONA_TEMPLATES_ES: Dict[str, List[Dict]] = {
    domain: _translate_personas(personas, _ES_NAME_MAP)
    for domain, personas in PERSONA_TEMPLATES.items()
}

GENERIC_PERSONAS_ES: List[Dict] = _translate_personas(GENERIC_PERSONAS, _ES_NAME_MAP)

PERSONA_TEMPLATES_PT: Dict[str, List[Dict]] = {
    domain: _translate_personas(personas, _PT_NAME_MAP)
    for domain, personas in PERSONA_TEMPLATES.items()
}

GENERIC_PERSONAS_PT: List[Dict] = _translate_personas(GENERIC_PERSONAS, _PT_NAME_MAP)


def load_persona_templates(agent_type: str, language: str = "English") -> List[Dict]:
    """
    Load pre-built persona templates for an agent type.
    Falls back to generic personas if the type isn't recognised.
    When *language* is ``"Spanish"`` or ``"Portuguese"`` the translated templates are returned.
    """
    if language == "Spanish":
        templates = PERSONA_TEMPLATES_ES.get(agent_type, [])
        if not templates:
            templates = GENERIC_PERSONAS_ES
    elif language == "Portuguese":
        templates = PERSONA_TEMPLATES_PT.get(agent_type, [])
        if not templates:
            templates = GENERIC_PERSONAS_PT
    else:
        templates = PERSONA_TEMPLATES.get(agent_type, [])
        if not templates:
            templates = GENERIC_PERSONAS
    return templates
