#!/usr/bin/env python3
"""
Step 4.2: Persona System
Select and manage personas for customer simulation
"""

import json
import random
from pathlib import Path
from typing import Dict, Optional

# Scenario-based persona weights
SCENARIO_PERSONA_WEIGHTS = {
    "booking_service_appointment": {
        "calm_cooperative": 0.3,
        "impatient_urgent": 0.2,
        "ultra_short": 0.15,
        "price_sensitive": 0.15,
        "need_it_today": 0.1,
        "friendly_chatty": 0.05,
        "confused_low_context": 0.05,
        "angry_escalating": 0.0
    },
    "status_update": {
        "impatient_urgent": 0.3,
        "angry_escalating": 0.25,
        "calm_cooperative": 0.2,
        "ultra_short": 0.15,
        "need_it_today": 0.1,
        "friendly_chatty": 0.0,
        "confused_low_context": 0.0,
        "price_sensitive": 0.0
    },
    "complaint_delay": {
        "angry_escalating": 0.4,
        "impatient_urgent": 0.3,
        "calm_cooperative": 0.15,
        "need_it_today": 0.1,
        "ultra_short": 0.05,
        "friendly_chatty": 0.0,
        "confused_low_context": 0.0,
        "price_sensitive": 0.0
    },
    "warranty_claim": {
        "calm_cooperative": 0.3,
        "confused_low_context": 0.25,
        "impatient_urgent": 0.2,
        "angry_escalating": 0.15,
        "ultra_short": 0.1,
        "friendly_chatty": 0.0,
        "need_it_today": 0.0,
        "price_sensitive": 0.0
    },
    "pricing_quote_dispute": {
        "price_sensitive": 0.4,
        "angry_escalating": 0.25,
        "calm_cooperative": 0.2,
        "confused_low_context": 0.15,
        "impatient_urgent": 0.0,
        "ultra_short": 0.0,
        "need_it_today": 0.0,
        "friendly_chatty": 0.0
    }
}


def load_personas(personas_file: Path) -> Dict:
    """Load persona definitions from JSON file."""
    if not personas_file.exists():
        raise FileNotFoundError(f"Personas file not found: {personas_file}")
    
    with open(personas_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def select_persona(scenario: str, stage: str = "opening", personas_dict: Optional[Dict] = None) -> str:
    """
    Select a persona based on scenario and stage.
    
    Args:
        scenario: Current scenario (e.g., "booking_service_appointment")
        stage: Current stage (default: "opening")
        personas_dict: Optional personas dict (loads from file if not provided)
    
    Returns:
        Selected persona ID (e.g., "calm_cooperative")
    """
    if personas_dict is None:
        base_dir = Path(__file__).parent.parent
        personas_file = base_dir / "personas.json"
        personas_dict = load_personas(personas_file)
    
    # Get weights for scenario
    if scenario in SCENARIO_PERSONA_WEIGHTS:
        weights = SCENARIO_PERSONA_WEIGHTS[scenario]
    else:
        # Default: equal weights
        all_personas = list(personas_dict.keys())
        weights = {p: 1.0 / len(all_personas) for p in all_personas}
    
    # Adjust by stage
    if stage == "escalation_complaint":
        # Higher chance of angry persona
        if "angry_escalating" in weights:
            weights["angry_escalating"] *= 2.0
        if "impatient_urgent" in weights:
            weights["impatient_urgent"] *= 1.5
    
    # Normalize weights
    total = sum(weights.values())
    if total > 0:
        weights = {k: v / total for k, v in weights.items()}
    
    # Select persona
    personas = list(weights.keys())
    probs = list(weights.values())
    selected = random.choices(personas, weights=probs, k=1)[0]
    
    return selected


def get_persona_traits(persona: str, personas_dict: Optional[Dict] = None) -> Dict:
    """
    Get traits and style for a persona.
    
    Args:
        persona: Persona ID (e.g., "calm_cooperative")
        personas_dict: Optional personas dict
    
    Returns:
        Persona definition dict
    """
    if personas_dict is None:
        base_dir = Path(__file__).parent.parent
        personas_file = base_dir / "personas.json"
        personas_dict = load_personas(personas_file)
    
    if persona not in personas_dict:
        raise ValueError(f"Unknown persona: {persona}")
    
    return personas_dict[persona]


def main():
    """Test persona selection."""
    base_dir = Path(__file__).parent.parent
    personas_file = base_dir / "personas.json"
    personas_dict = load_personas(personas_file)
    
    print("Available personas:")
    for persona_id, persona_data in personas_dict.items():
        print(f"  {persona_id}: {persona_data['name']}")
    
    print("\nTesting persona selection:\n")
    
    test_scenarios = [
        "booking_service_appointment",
        "status_update",
        "complaint_delay",
        "pricing_quote_dispute"
    ]
    
    for scenario in test_scenarios:
        selected = select_persona(scenario, personas_dict=personas_dict)
        traits = get_persona_traits(selected, personas_dict)
        print(f"Scenario: {scenario}")
        print(f"  Selected: {selected} ({traits['name']})")
        print(f"  Description: {traits['description']}")
        print()


if __name__ == "__main__":
    main()
