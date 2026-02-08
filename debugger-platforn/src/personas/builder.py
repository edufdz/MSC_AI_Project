"""
PersonaBuilder: creates, manages, and exports synthetic user personas
for agent testing.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import anthropic
from dotenv import load_dotenv

from src.personas.models import (
    Persona, PersonaLibrary,
    PersonaTraits, PersonaStyle, PersonaEdgeBehaviors,
)
from src.personas.templates import load_persona_templates, GENERIC_PERSONAS

# Load .env from project root
_project_root = Path(__file__).parent.parent.parent
load_dotenv(_project_root / ".env")

MODEL = "claude-haiku-4-5"  # Switched to Haiku for cost savings (~67% cheaper)


class PersonaBuilder:
    """
    Builds a library of synthetic user personas from templates,
    AI generation, or manual input.
    """

    def __init__(self, agent_map: Dict):
        self.agent_map = agent_map
        self.agent_type: str = agent_map.get("metadata", {}).get("type", "custom")
        self.agent_purpose: str = agent_map.get("metadata", {}).get("purpose", "")
        self.personas: List[Persona] = []

    # ------------------------------------------------------------------
    # Template loading
    # ------------------------------------------------------------------

    def load_templates(self, selected_names: Optional[List[str]] = None) -> List[Persona]:
        """
        Load persona templates matching the agent's domain.
        Optionally filter by name.
        """
        templates = load_persona_templates(self.agent_type)

        if selected_names:
            templates = [t for t in templates if t["name"] in selected_names]

        for tpl in templates:
            persona = Persona(
                persona_id=str(uuid.uuid4()),
                name=tpl["name"],
                agent_type=self.agent_type,
                source="template",
                traits=PersonaTraits(**tpl["traits"]),
                style=PersonaStyle(**tpl["style"]),
                edge_behaviors=PersonaEdgeBehaviors(**tpl.get("edge_behaviors", {})),
                sample_messages=[],
                created_at=datetime.now(timezone.utc),
            )
            self.personas.append(persona)

        return self.personas

    # ------------------------------------------------------------------
    # AI-powered persona generation
    # ------------------------------------------------------------------

    def generate_personas(self, count: int = 3) -> List[Persona]:
        """
        Use Claude to generate novel personas tailored to the agent's
        purpose and tool set.
        """
        tool_names = [t["name"] for t in self.agent_map.get("components", {}).get("tools", [])]
        risks = self.agent_map.get("risk_flags", {})

        prompt = f"""You are designing synthetic user personas to test an AI agent.

Agent info:
- Type: {self.agent_type}
- Purpose: {self.agent_purpose}
- Tools available: {', '.join(tool_names) if tool_names else 'unknown'}
- Has PII handling: {risks.get('pii_handling', False)}
- Critical actions: {risks.get('critical_actions', [])}

Generate exactly {count} diverse personas. Each persona should test a different
aspect of the agent (happy path, edge cases, adversarial, etc.).

Return ONLY valid JSON (no markdown fences):
{{
  "personas": [
    {{
      "name": "Persona Name",
      "traits": {{
        "patience": 5,
        "clarity": 5,
        "tech_savviness": 5,
        "politeness": 5,
        "verbosity": 5
      }},
      "style": {{
        "tone": "neutral",
        "formality": "casual",
        "typo_rate": 0.05,
        "abbreviation_use": "low",
        "emoji_use": "none"
      }},
      "edge_behaviors": {{
        "rage_quits": false,
        "changes_mind": false,
        "provides_incomplete_info": false,
        "asks_off_topic": false,
        "tests_boundaries": false
      }},
      "rationale": "why this persona is useful for testing"
    }}
  ]
}}"""

        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        import json, re
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)

        data = json.loads(raw)
        generated = []

        for p in data.get("personas", []):
            persona = Persona(
                persona_id=str(uuid.uuid4()),
                name=p["name"],
                agent_type=self.agent_type,
                source="ai_generated",
                traits=PersonaTraits(**p["traits"]),
                style=PersonaStyle(**p["style"]),
                edge_behaviors=PersonaEdgeBehaviors(**p.get("edge_behaviors", {})),
                sample_messages=[],
                created_at=datetime.now(timezone.utc),
            )
            generated.append(persona)
            self.personas.append(persona)

        return generated

    # ------------------------------------------------------------------
    # Sample message generation
    # ------------------------------------------------------------------

    def generate_sample_messages(
        self, persona: Persona, count: int = 3,
    ) -> List[str]:
        """
        Generate example messages that this persona would send to the agent.
        """
        tool_names = [t["name"] for t in self.agent_map.get("components", {}).get("tools", [])]

        edge_list = [k for k, v in persona.edge_behaviors.model_dump().items() if v]
        edge_desc = ", ".join(edge_list) if edge_list else "none"

        # Detect language from agent_map
        language = self.agent_map.get("metadata", {}).get("conversation_language", "English")
        lang_instruction = f"\nIMPORTANT: Generate all messages in {language}." if language != "English" else ""

        prompt = f"""Generate exactly {count} example messages that this user persona
would send to a {self.agent_type} agent whose purpose is: {self.agent_purpose}
{lang_instruction}

Persona: {persona.name}
Traits: patience={persona.traits.patience}/10, clarity={persona.traits.clarity}/10, \
tech_savviness={persona.traits.tech_savviness}/10, politeness={persona.traits.politeness}/10, \
verbosity={persona.traits.verbosity}/10
Style: tone={persona.style.tone}, formality={persona.style.formality}, \
typo_rate={persona.style.typo_rate}, abbreviations={persona.style.abbreviation_use}, \
emojis={persona.style.emoji_use}
Edge behaviors: {edge_desc}
Available tools the agent has: {', '.join(tool_names) if tool_names else 'general'}

Each message should feel natural and reflect the persona's traits faithfully.
If typo_rate > 0, include realistic typos proportionally.
If the persona has edge behaviors, at least one message should demonstrate them.

Return ONLY a JSON array of strings (no markdown fences):
["message 1", "message 2", "message 3"]"""

        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        import json, re
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)

        messages = json.loads(raw)
        persona.sample_messages.extend(messages)
        return messages

    # ------------------------------------------------------------------
    # Custom persona creation
    # ------------------------------------------------------------------

    def create_custom(self, persona_data: Dict) -> Persona:
        """Create a persona from user-supplied data."""
        persona = Persona(
            persona_id=str(uuid.uuid4()),
            name=persona_data["name"],
            agent_type=persona_data.get("agent_type", self.agent_type),
            source="custom",
            traits=PersonaTraits(**persona_data["traits"]),
            style=PersonaStyle(**persona_data["style"]),
            edge_behaviors=PersonaEdgeBehaviors(**persona_data.get("edge_behaviors", {})),
            sample_messages=persona_data.get("sample_messages", []),
            created_at=datetime.now(timezone.utc),
        )
        self.personas.append(persona)
        return persona

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_library(self) -> PersonaLibrary:
        """Export all personas as a PersonaLibrary."""
        return PersonaLibrary(
            persona_library_id=str(uuid.uuid4()),
            agent_id=self.agent_map.get("agent_id", "unknown"),
            personas=self.personas,
            created_at=datetime.now(timezone.utc),
        )
