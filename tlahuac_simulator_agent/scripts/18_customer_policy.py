#!/usr/bin/env python3
"""
Step 4.1: Customer Policy
Decide next customer action based on conversation state
"""

import random
from typing import Dict, Optional, List
from collections import Counter

# Import intent detection for semantic repeat checking
try:
    import sys
    from pathlib import Path
    scripts_dir = Path(__file__).parent
    intent_module_path = scripts_dir / "24_customer_intent.py"
    if intent_module_path.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("customer_intent", intent_module_path)
        customer_intent = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(customer_intent)
        is_semantic_repeat = customer_intent.is_semantic_repeat
    else:
        is_semantic_repeat = None
except Exception:
    is_semantic_repeat = None

# Action definitions
ACTIONS = [
    "answer_question",
    "ask_clarification",
    "ask_status",
    "reject_proposal",
    "provide_constraint",
    "complain_escalate",
    "short_ack",
    "switch_topic",
    # New strategy actions
    "clarify_question",
    "add_details",
    "reduce_request",
    "change_channel",
    "compare_elsewhere",
    "threaten_leave",
    "leave_chat",
    "come_back_later"
]


def decide_action(
    scenario: str,
    stage: str,
    dealership_asked_question: bool,
    turn_count: int,
    persona: str,
    last_dealership_turn: Optional[str] = None,
    dealer_response_type: Optional[str] = None,
    customer_state: Optional[Dict] = None,
    last_customer_turns: Optional[List[Dict]] = None
) -> Dict[str, any]:
    """
    Decide next customer action based on state.
    
    Args:
        scenario: Current scenario (e.g., "booking_service_appointment")
        stage: Current stage (e.g., "scheduling")
        dealership_asked_question: Whether last dealership turn was a question
        turn_count: Number of turns in conversation so far
        persona: Current persona (e.g., "calm_cooperative")
        last_dealership_turn: Last dealership message text (optional)
        dealer_response_type: Type of dealer response ("helpful", "uncertain", "blocking", "rude")
        customer_state: Dict with goal_intent, attempts_same_goal, frustration, patience, strategy
        last_customer_turns: List of recent customer turns for semantic repeat detection
    
    Returns:
        {
            "action": "answer_question",
            "reasoning": "Dealership asked for kilometraje",
            "urgency": 0.3,
            "strategy_switch_reason": None
        }
    """
    # Base probabilities by action
    action_probs = {
        "answer_question": 0.0,
        "ask_clarification": 0.0,
        "ask_status": 0.0,
        "reject_proposal": 0.0,
        "provide_constraint": 0.0,
        "complain_escalate": 0.0,
        "short_ack": 0.0,
        "switch_topic": 0.0,
        # Strategy actions
        "clarify_question": 0.0,
        "add_details": 0.0,
        "reduce_request": 0.0,
        "change_channel": 0.0,
        "compare_elsewhere": 0.0,
        "threaten_leave": 0.0,
        "leave_chat": 0.0,
        "come_back_later": 0.0
    }
    
    # Extract customer state
    goal_intent = None
    attempts_same_goal = 0
    frustration = 0.0
    patience = 0.5
    current_strategy = None
    
    if customer_state:
        goal_intent = customer_state.get("goal_intent")
        attempts_same_goal = customer_state.get("attempts_same_goal", 0)
        frustration = customer_state.get("frustration", 0.0)
        patience = customer_state.get("patience", 0.5)
        current_strategy = customer_state.get("strategy")
    
    strategy_switch_reason = None
    
    # Check for semantic repeats in last customer turns
    has_semantic_repeat = False
    if last_customer_turns and is_semantic_repeat:
        customer_turns = [t for t in last_customer_turns if t.get('role') == 'customer']
        if len(customer_turns) >= 2:
            # Check last 3 customer turns for semantic repeats
            recent_turns = customer_turns[-3:]
            for i in range(len(recent_turns) - 1):
                turn1 = recent_turns[i]
                turn2 = recent_turns[i + 1]
                text1 = turn1.get('text', '')
                text2 = turn2.get('text', '')
                intent1 = turn1.get('metadata', {}).get('intent', 'general_question')
                intent2 = turn2.get('metadata', {}).get('intent', 'general_question')
                
                if is_semantic_repeat(intent1, intent2, text1, text2):
                    has_semantic_repeat = True
                    break
    
    # Get scenario-specific strategies if available
    scenario_strategies = None
    if customer_state and 'scenario_strategies' in customer_state:
        scenario_strategies = customer_state['scenario_strategies']
    
    # Strategy switching logic based on dealer response type
    if dealer_response_type == "uncertain":
        if attempts_same_goal >= 1:
            # Force strategy switch after one re-ask
            strategy_switch_reason = "Dealer uncertain after re-ask"
            # Block answer_question if it would repeat
            action_probs["answer_question"] = -1.0  # Block
            
            # Force strategy actions
            action_probs["clarify_question"] = 0.4
            action_probs["add_details"] = 0.3
            action_probs["reduce_request"] = 0.3
    
    elif dealer_response_type == "blocking":
        strategy_switch_reason = "Dealer blocking request"
        # Block normal actions
        action_probs["answer_question"] = -1.0
        action_probs["ask_clarification"] = -1.0
        
        # Force exit/alternative strategies
        action_probs["change_channel"] = 0.4
        action_probs["come_back_later"] = 0.3
        action_probs["leave_chat"] = 0.3
    
    elif dealer_response_type == "rude":
        strategy_switch_reason = "Dealer rude/low-effort"
        # Increase frustration impact
        frustration = min(1.0, frustration + 0.25)
        
        # Force escalation/exit strategies
        action_probs["threaten_leave"] = 0.5
        action_probs["leave_chat"] = 0.4
        action_probs["complain_escalate"] = 0.1
    
    elif dealer_response_type == "helpful":
        # When dealer is helpful, acknowledge and move forward
        strategy_switch_reason = "Dealer provided helpful information"
        
        # Reduce frustration
        frustration = max(0.0, frustration - 0.15)
        
        # Encourage cooperative actions
        if dealership_asked_question:
            # If dealer asked a question, answer it
            action_probs["answer_question"] = 0.6
            action_probs["short_ack"] = 0.2
            action_probs["provide_constraint"] = 0.2
        else:
            # If dealer provided info, acknowledge and continue
            action_probs["short_ack"] = 0.5
            action_probs["answer_question"] = 0.3  # In case they need to provide info
            action_probs["ask_clarification"] = 0.2  # Only if still unclear
        
        # Block threatening/leaving when dealer is helpful
        action_probs["threaten_leave"] = -1.0
        action_probs["leave_chat"] = -1.0
        action_probs["complain_escalate"] = -1.0
    
    # Hard constraint: block semantic repeats
    if has_semantic_repeat:
        strategy_switch_reason = "Semantic repeat detected"
        # Block actions that would repeat
        action_probs["answer_question"] = -1.0
        action_probs["ask_clarification"] = -1.0
        
        # Force different strategy
        if dealer_response_type == "uncertain":
            action_probs["clarify_question"] = 0.5
            action_probs["add_details"] = 0.5
        elif dealer_response_type == "blocking":
            action_probs["change_channel"] = 0.5
            action_probs["leave_chat"] = 0.5
        else:
            # Default: try different approach
            action_probs["reduce_request"] = 0.4
            action_probs["add_details"] = 0.3
            action_probs["change_channel"] = 0.3
    
    # Rule 1: If dealership asked question
    if dealership_asked_question:
        if persona == "ultra_short":
            action_probs["short_ack"] = 0.5
            action_probs["answer_question"] = 0.4
            action_probs["ask_clarification"] = 0.1
        else:
            action_probs["answer_question"] = 0.7
            action_probs["ask_clarification"] = 0.2
            action_probs["short_ack"] = 0.1
    else:
        # Rule 2: By stage
        if stage == "opening":
            action_probs["answer_question"] = 0.4
            action_probs["ask_clarification"] = 0.4
            action_probs["short_ack"] = 0.2
        
        elif stage == "info_gathering":
            action_probs["answer_question"] = 0.6
            action_probs["provide_constraint"] = 0.3
            action_probs["ask_clarification"] = 0.1
        
        elif stage == "scheduling":
            action_probs["answer_question"] = 0.5
            action_probs["reject_proposal"] = 0.3
            action_probs["provide_constraint"] = 0.2
        
        elif stage == "waiting_status_loop":
            action_probs["ask_status"] = 0.6
            action_probs["complain_escalate"] = 0.3
            action_probs["short_ack"] = 0.1
        
        elif stage == "resolution":
            action_probs["short_ack"] = 0.7
            action_probs["ask_status"] = 0.2
            action_probs["complain_escalate"] = 0.1
        
        elif stage == "closing":
            action_probs["short_ack"] = 0.8
            action_probs["switch_topic"] = 0.2
        
        else:  # escalation_complaint or unknown
            action_probs["complain_escalate"] = 0.5
            action_probs["ask_status"] = 0.3
            action_probs["short_ack"] = 0.2
    
    # Rule 3: Adjust by persona
    persona_adjustments = {
        "impatient_urgent": {
            "ask_status": +0.2,
            "complain_escalate": +0.1,
            "short_ack": -0.1
        },
        "angry_escalating": {
            "complain_escalate": +0.3,
            "answer_question": -0.2,
            "short_ack": -0.1
        },
        "ultra_short": {
            "short_ack": +0.3,
            "answer_question": -0.2,
            "ask_clarification": -0.1
        },
        "calm_cooperative": {
            "answer_question": +0.1,
            "complain_escalate": -0.1
        },
        "price_sensitive": {
            "provide_constraint": +0.2,
            "ask_clarification": +0.1
        },
        "need_it_today": {
            "reject_proposal": +0.2,
            "provide_constraint": +0.1,
            "complain_escalate": +0.1
        },
        "confused_low_context": {
            "ask_clarification": +0.3,
            "answer_question": -0.1
        },
        "friendly_chatty": {
            "switch_topic": +0.1,
            "short_ack": -0.1
        }
    }
    
    if persona in persona_adjustments:
        for action, adjustment in persona_adjustments[persona].items():
            action_probs[action] = max(0.0, min(1.0, action_probs[action] + adjustment))
    
    # Rule 4: Adjust by turn count
    if turn_count < 5:
        # Early turns: more cooperative
        action_probs["answer_question"] += 0.1
        action_probs["ask_clarification"] += 0.05
        action_probs["complain_escalate"] -= 0.1
    elif turn_count > 15:
        # Late turns: more status checks, shorter responses
        action_probs["ask_status"] += 0.1
        action_probs["short_ack"] += 0.1
        action_probs["complain_escalate"] += 0.05
        action_probs["answer_question"] -= 0.1
    
    # Remove blocked actions (negative probabilities)
    action_probs = {k: max(0.0, v) for k, v in action_probs.items()}
    
    # Normalize probabilities
    total = sum(action_probs.values())
    if total > 0:
        action_probs = {k: v / total for k, v in action_probs.items()}
    else:
        # Fallback: equal probability (only non-blocked actions)
        valid_actions = [k for k, v in action_probs.items() if v >= 0]
        if valid_actions:
            action_probs = {k: 1.0 / len(valid_actions) if k in valid_actions else 0.0 for k in ACTIONS}
        else:
            # Last resort: allow all actions
            action_probs = {k: 1.0 / len(ACTIONS) for k in ACTIONS}
    
    # Select action based on probabilities
    actions = list(action_probs.keys())
    weights = list(action_probs.values())
    selected_action = random.choices(actions, weights=weights, k=1)[0]
    
    # Generate reasoning
    reasoning_parts = []
    if dealership_asked_question:
        reasoning_parts.append("Dealership asked a question")
    reasoning_parts.append(f"Stage: {stage}")
    reasoning_parts.append(f"Persona: {persona}")
    if turn_count > 15:
        reasoning_parts.append("Late in conversation")
    
    reasoning = ", ".join(reasoning_parts)
    
    # Calculate urgency (0.0-1.0)
    urgency = 0.3  # Base
    if persona in ["impatient_urgent", "need_it_today"]:
        urgency += 0.3
    if stage == "waiting_status_loop":
        urgency += 0.2
    if selected_action == "complain_escalate":
        urgency += 0.2
    urgency = min(1.0, urgency)
    
    return {
        "action": selected_action,
        "reasoning": reasoning,
        "urgency": urgency,
        "probabilities": action_probs,  # For debugging
        "strategy_switch_reason": strategy_switch_reason
    }


def main():
    """Test the policy function."""
    # Test cases
    test_cases = [
        {
            "scenario": "booking_service_appointment",
            "stage": "info_gathering",
            "dealership_asked_question": True,
            "turn_count": 3,
            "persona": "calm_cooperative"
        },
        {
            "scenario": "booking_service_appointment",
            "stage": "scheduling",
            "dealership_asked_question": False,
            "turn_count": 8,
            "persona": "impatient_urgent"
        },
        {
            "scenario": "status_update",
            "stage": "waiting_status_loop",
            "dealership_asked_question": False,
            "turn_count": 12,
            "persona": "angry_escalating"
        }
    ]
    
    print("Testing customer policy:\n")
    for i, test in enumerate(test_cases, 1):
        result = decide_action(**test)
        print(f"Test {i}:")
        print(f"  Input: {test}")
        print(f"  Action: {result['action']}")
        print(f"  Reasoning: {result['reasoning']}")
        print(f"  Urgency: {result['urgency']:.2f}")
        print()


if __name__ == "__main__":
    main()
