#!/usr/bin/env python3
"""
Phase 5: Chat Simulator
Interactive chatbot where user plays dealership and system simulates customer
"""

import sys
import os
import re
import random
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import components
import importlib.util

# Load modules dynamically
def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

scripts_dir = Path(__file__).parent / "scripts"
customer_policy = load_module("customer_policy", scripts_dir / "18_customer_policy.py")
personas_module = load_module("personas", scripts_dir / "19_personas.py")
prompt_template = load_module("prompt_template", scripts_dir / "20_prompt_template.py")
filters_module = load_module("filters", scripts_dir / "21_filters.py")
logging_module = load_module("logging", scripts_dir / "22_logging.py")
dealer_response_module = load_module("dealer_response", scripts_dir / "23_dealer_response.py")
customer_intent_module = load_module("customer_intent", scripts_dir / "24_customer_intent.py")
message_variation_module = load_module("message_variation", scripts_dir / "25_message_variation.py")

# Import functions
decide_action = customer_policy.decide_action
select_persona = personas_module.select_persona
get_persona_traits = personas_module.get_persona_traits
load_personas = personas_module.load_personas
build_prompt = prompt_template.build_prompt
call_llm = prompt_template.call_llm
filter_message = filters_module.filter_message
init_run_log = logging_module.init_run_log
log_turn = logging_module.log_turn
finalize_run = logging_module.finalize_run
classify_dealer_response = dealer_response_module.classify_dealer_response
detect_customer_intent = customer_intent_module.detect_customer_intent
render_customer_messages = message_variation_module.render_customer_messages
apply_imperfections = message_variation_module.apply_imperfections

# Import retriever
retriever_path = Path(__file__).parent / "retriever.py"
retriever_module = load_module("retriever", retriever_path)
CustomerRetriever = retriever_module.CustomerRetriever

# Configuration
DEFAULT_SCENARIO = "booking_service_appointment"
MAX_TURNS = 50
MAX_MESSAGE_LENGTH = 240


def detect_question(text: str) -> bool:
    """Detect if text is a question."""
    if not text:
        return False
    
    # Check for question mark
    if '?' in text:
        return True
    
    # Check for question words (Spanish)
    question_words = [
        r'\bqu[ée]\b', r'\bcu[áa]ndo\b', r'\bc[óo]mo\b', r'\bd[óo]nde\b',
        r'\bcu[áa]nto\b', r'\bcu[áa]l\b', r'\bqui[ée]n\b', r'\bpor qu[ée]\b'
    ]
    
    text_lower = text.lower()
    for pattern in question_words:
        if re.search(pattern, text_lower):
            return True
    
    return False


def update_stage(state: Dict) -> str:
    """Update conversation stage based on flow."""
    turns = state.get('turns', [])
    turn_count = state.get('turn_count', 0)
    current_stage = state.get('stage', 'opening')
    
    # Get recent turns text
    recent_text = ' '.join([t.get('text', '') for t in turns[-4:]])
    recent_lower = recent_text.lower()
    
    # Stage detection keywords
    if turn_count <= 2:
        return 'opening'
    
    # Scheduling keywords
    if any(word in recent_lower for word in ['día', 'horario', 'fecha', 'disponibilidad', 'cita', 'agendar']):
        return 'scheduling'
    
    # Info gathering keywords
    if any(word in recent_lower for word in ['kilometraje', 'modelo', 'año', 'qué servicio', 'cuál']):
        return 'info_gathering'
    
    # Waiting/status keywords
    if any(word in recent_lower for word in ['ya está listo', 'cuándo estará', 'sigue en taller', 'avance']):
        return 'waiting_status_loop'
    
    # Resolution keywords
    if any(word in recent_lower for word in ['ya quedó', 'listo para recoger', 'gracias', 'perfecto']):
        return 'resolution'
    
    # Closing keywords
    if any(word in recent_lower for word in ['hasta luego', 'cualquier duda', 'quedamos pendientes']):
        return 'closing'
    
    # Escalation keywords
    if any(word in recent_lower for word in ['gerente', 'queja', 'mal servicio', 'insatisfecho']):
        return 'escalation_complaint'
    
    # Default: maintain current stage or progress
    stage_progression = {
        'opening': 'info_gathering',
        'info_gathering': 'scheduling',
        'scheduling': 'waiting_status_loop',
        'waiting_status_loop': 'resolution',
        'resolution': 'closing',
        'closing': 'closing',
        'escalation_complaint': 'escalation_complaint'
    }
    
    # Progress stage if conversation is long enough
    if turn_count > 10 and current_stage in stage_progression:
        # Check if we should progress
        if current_stage == 'scheduling' and turn_count > 8:
            return 'waiting_status_loop'
        elif current_stage == 'waiting_status_loop' and turn_count > 15:
            return 'resolution'
    
    return current_stage


def get_last_turns(turns: List[Dict], role: str, count: int) -> List[str]:
    """Get last N turns of specified role."""
    role_turns = [t for t in turns if t.get('role') == role]
    return [t.get('text', '') for t in role_turns[-count:]]


def _select_persona_from_weights(persona_weights: Dict[str, float], personas_dict: Dict) -> str:
    """Select persona from variant-specific weights."""
    # Normalize weights
    total = sum(persona_weights.values())
    if total > 0:
        normalized_weights = {k: v / total for k, v in persona_weights.items()}
    else:
        # Fallback to equal weights
        normalized_weights = {p: 1.0 / len(personas_dict) for p in personas_dict.keys()}
    
    # Select
    personas = list(normalized_weights.keys())
    probs = list(normalized_weights.values())
    return random.choices(personas, weights=probs, k=1)[0]


def get_persona_patience(persona: str) -> float:
    """
    Get patience level for a persona (0.0-1.0).
    
    Args:
        persona: Persona name
    
    Returns:
        Patience level (higher = more patient)
    """
    patience_map = {
        "impatient_urgent": 0.3,
        "angry_escalating": 0.2,
        "ultra_short": 0.4,
        "calm_cooperative": 0.8,
        "price_sensitive": 0.6,
        "need_it_today": 0.3,
        "confused_low_context": 0.5,
        "friendly_chatty": 0.7
    }
    return patience_map.get(persona, 0.5)


def generate_run_id() -> str:
    """Generate unique run ID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"run_{timestamp}"


def handle_command(command: str, state: Dict) -> bool:
    """Handle special commands. Returns True if command handled, False otherwise."""
    cmd = command.lower().strip()
    
    if cmd == 'help':
        print("\nAvailable commands:")
        print("  quit/exit/q - End conversation")
        print("  debug - Toggle debug output")
        print("  stage - Show current stage")
        print("  persona - Show current persona")
        print("  reset - Start new conversation")
        print("  help - Show this help")
        return True
    
    elif cmd in ['stage']:
        print(f"\nCurrent stage: {state.get('stage')}")
        return True
    
    elif cmd in ['persona']:
        print(f"\nCurrent persona: {state.get('persona')}")
        persona_data = get_persona_traits(state.get('persona'))
        print(f"Description: {persona_data.get('description')}")
        return True
    
    elif cmd == 'reset':
        print("\nResetting conversation...")
        return 'reset'
    
    elif cmd == 'debug':
        state['debug_mode'] = not state.get('debug_mode', False)
        print(f"\nDebug mode: {'ON' if state['debug_mode'] else 'OFF'}")
        return True
    
    return False


def main():
    """Main chat simulator loop."""
    print("=" * 60)
    print("Customer Simulator")
    print("=" * 60)
    print("\nYou play the dealership. The system simulates the customer.")
    print("Type 'quit' to exit, 'help' for commands\n")
    
    # Initialize retriever
    try:
        retriever = CustomerRetriever(index_dir="vector_index")
        print("✓ Retrieval system loaded")
    except Exception as e:
        print(f"Error loading retriever: {e}")
        print("Make sure you've run scripts/16_build_index.py first!")
        return
    
    # Load personas
    base_dir = Path(__file__).parent
    personas_file = base_dir / "personas.json"
    personas_dict = load_personas(personas_file)
    print(f"✓ Loaded {len(personas_dict)} personas")
    
    # Load scenarios
    scenarios_file = base_dir / "scenarios.json"
    scenarios_dict = {}
    if scenarios_file.exists():
        with open(scenarios_file, 'r', encoding='utf-8') as f:
            scenarios_data = json.load(f)
            scenarios_dict = scenarios_data.get('scenarios', {})
    
    # Load scenario variants
    variants_file = base_dir / "scenario_variants.json"
    variants_dict = {}
    if variants_file.exists():
        with open(variants_file, 'r', encoding='utf-8') as f:
            variants_dict = json.load(f)
    
    # Select scenario (weighted by category or use default)
    if scenarios_dict:
        # For now, use DEFAULT_SCENARIO or random selection
        # TODO: Implement weighted selection by category
        if DEFAULT_SCENARIO in scenarios_dict:
            scenario = DEFAULT_SCENARIO
        else:
            scenario = random.choice(list(scenarios_dict.keys()))
    else:
        scenario = DEFAULT_SCENARIO
    
    # Select variant if available
    selected_variant = None
    if scenario in variants_dict:
        variant_data = variants_dict[scenario]
        variants = variant_data.get('variants', [])
        if variants:
            selected_variant = random.choice(variants)
    
    # Initialize conversation
    seed = random.randint(1, 1000000)
    random.seed(seed)
    
    # Select persona (consider variant if available)
    if selected_variant and 'persona_weights' in selected_variant:
        # Use variant-specific persona weights
        persona = _select_persona_from_weights(selected_variant['persona_weights'], personas_dict)
    else:
        persona = select_persona(scenario, "opening", personas_dict)
    persona_data = get_persona_traits(persona, personas_dict)
    
    run_id = generate_run_id()
    log_file = init_run_log(run_id, scenario, persona, seed)
    
    state = {
        "conversation_id": run_id,
        "scenario": scenario,
        "stage": "opening",
        "persona": persona,
        "turn_count": 0,
        "turns": [],
        "started_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed": seed,
        "debug_mode": False,
        # New state variables for strategy switching
        "goal_intent": None,
        "attempts_same_goal": 0,
        "frustration": 0.0,
        "patience": get_persona_patience(persona),
        "strategy": None,
        "last_customer_intents": []
    }
    
    print(f"\nScenario: {scenario}")
    if selected_variant:
        print(f"Variant: {selected_variant.get('variant_id', 'unknown')}")
    print(f"Persona: {persona_data['name']}")
    print(f"Stage: {state['stage']}")
    print(f"Run ID: {run_id}")
    print("\n" + "-" * 60 + "\n")
    
    # Use starter opener for first customer message if available
    initial_customer_message = None
    if scenarios_dict and scenario in scenarios_dict:
        scenario_data = scenarios_dict[scenario]
        starter_openers = scenario_data.get('starter_openers', [])
        if starter_openers:
            initial_customer_message = random.choice(starter_openers)
            print(f"Customer: {initial_customer_message}\n")
    
    # Chat loop
    while True:
        try:
            # Get dealership input
            dealership_message = input("Dealership: ").strip()
            
            if not dealership_message:
                continue
            
            # Handle commands
            cmd_result = handle_command(dealership_message, state)
            if cmd_result == 'reset':
                # Reset conversation
                seed = random.randint(1, 1000000)
                random.seed(seed)
                persona = select_persona(scenario, "opening", personas_dict)
                persona_data = get_persona_traits(persona, personas_dict)
                run_id = generate_run_id()
                log_file = init_run_log(run_id, scenario, persona, seed)
                state = {
                    "conversation_id": run_id,
                    "scenario": scenario,
                    "stage": "opening",
                    "persona": persona,
                    "turn_count": 0,
                    "turns": [],
                    "started_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "seed": seed,
                    "debug_mode": state.get('debug_mode', False),
                    # New state variables for strategy switching
                    "goal_intent": None,
                    "attempts_same_goal": 0,
                    "frustration": 0.0,
                    "patience": get_persona_patience(persona),
                    "strategy": None,
                    "last_customer_intents": []
                }
                print(f"\nNew conversation started. Persona: {persona_data['name']}\n")
                continue
            elif cmd_result:
                continue
            
            # Check for quit
            if dealership_message.lower() in ['quit', 'exit', 'q']:
                break
            
            # Check turn limit
            if state['turn_count'] >= MAX_TURNS:
                print(f"\nMaximum turns ({MAX_TURNS}) reached. Ending conversation.")
                break
            
            # Update conversation state
            state['turns'].append({
                'role': 'dealership',
                'text': dealership_message,
                'turn_idx': state['turn_count']
            })
            state['turn_count'] += 1
            
            # Detect if dealership asked question
            dealership_asked_question = detect_question(dealership_message)
            
            # Classify dealer response (with context from last customer turn)
            last_customer_turn_text = None
            if state['turns']:
                last_customer_turns = [t for t in state['turns'] if t.get('role') == 'customer']
                if last_customer_turns:
                    last_customer_turn_text = last_customer_turns[-1].get('text', '')
            
            dealer_response_classification = classify_dealer_response(
                dealership_message, 
                previous_customer_turn=last_customer_turn_text
            )
            dealer_response_type = dealer_response_classification['type']
            
            # Detect customer intent from last customer turn (if exists)
            last_customer_turn = None
            if state['turns']:
                customer_turns = [t for t in state['turns'] if t.get('role') == 'customer']
                if customer_turns:
                    last_customer_turn = customer_turns[-1]
                    customer_text = last_customer_turn.get('text', '')
                    if customer_text:
                        intent_result = detect_customer_intent(customer_text, state['turns'][-6:])
                        detected_intent = intent_result['intent']
                        
                        # Update goal_intent and attempts_same_goal
                        if state['goal_intent'] == detected_intent:
                            state['attempts_same_goal'] += 1
                        else:
                            state['goal_intent'] = detected_intent
                            state['attempts_same_goal'] = 1
            
            # Update frustration based on dealer response
            if dealer_response_type == "uncertain":
                state['frustration'] = min(1.0, state['frustration'] + 0.15)
            elif dealer_response_type == "blocking":
                state['frustration'] = min(1.0, state['frustration'] + 0.25)
            elif dealer_response_type == "rude":
                state['frustration'] = min(1.0, state['frustration'] + 0.25)
            elif dealer_response_type == "helpful":
                state['frustration'] = max(0.0, state['frustration'] - 0.15)
                # Reset attempts when dealer is helpful (they're making progress)
                if state['attempts_same_goal'] > 0:
                    state['attempts_same_goal'] = max(0, state['attempts_same_goal'] - 1)
            
            # Update stage
            state['stage'] = update_stage(state)
            
            # Get scenario-specific strategies
            scenario_strategies = None
            if scenarios_dict and scenario in scenarios_dict:
                scenario_data = scenarios_dict[scenario]
                scenario_strategies = scenario_data.get('common_customer_strategies', [])
            
            # Prepare customer state for policy
            customer_state = {
                'goal_intent': state['goal_intent'],
                'attempts_same_goal': state['attempts_same_goal'],
                'frustration': state['frustration'],
                'patience': state['patience'],
                'strategy': state['strategy'],
                'scenario_strategies': scenario_strategies
            }
            
            # Decide customer action
            action = decide_action(
                scenario=state['scenario'],
                stage=state['stage'],
                dealership_asked_question=dealership_asked_question,
                turn_count=state['turn_count'],
                persona=state['persona'],
                last_dealership_turn=dealership_message,
                dealer_response_type=dealer_response_type,
                customer_state=customer_state,
                last_customer_turns=state['turns'][-6:]
            )
            
            # Update strategy
            state['strategy'] = action['action']
            
            # Retrieve anchors
            context = {
                'last_dealership_turns': get_last_turns(state['turns'], 'dealership', 2),
                'last_customer_turns': get_last_turns(state['turns'], 'customer', 2)
            }
            
            try:
                anchors = retriever.get_anchors(
                    context,
                    k=8,
                    scenario=state['scenario'],
                    stage=state['stage']
                )
            except Exception as e:
                print(f"Warning: Retrieval failed: {e}, using empty anchors")
                anchors = []
            
            # Build prompt
            try:
                prompt = build_prompt(
                    context={'turns': state['turns'][-6:]},
                    persona=persona_data,
                    scenario=state['scenario'],
                    stage=state['stage'],
                    action=action,
                    anchors=anchors,
                    customer_state=customer_state
                )
            except Exception as e:
                print(f"Error building prompt: {e}")
                # Fallback response
                llm_messages = ["Ok"]
                llm_intent = 'general_question'
                llm_strategy = action.get('action', 'answer_question')
                filter_result = {
                    'filtered_message': "Ok",
                    'was_filtered': False,
                    'filters_applied': [],
                    'pii_found': [],
                    'is_copying': False,
                    'max_similarity': 0.0,
                    'content_valid': True,
                    'issues': []
                }
                # Process fallback message
                processed_messages = []
                filtered_msg = filter_result['filtered_message']
                filtered_msg = apply_imperfections(filtered_msg, state['persona'])
                msg_bursts = render_customer_messages(filtered_msg, state['persona'])
                processed_messages.extend(msg_bursts)
                message_bursts = processed_messages
                combined_for_intent = " ".join(message_bursts)
                detected_intent = llm_intent
            else:
                # Generate customer response
                start_time = time.time()
                try:
                    llm_response = call_llm(prompt)
                    
                    # Extract messages array (new format) or handle old format
                    llm_messages = llm_response.get('messages', [])
                    if not llm_messages:
                        # Fallback to old format or default
                        llm_messages = [llm_response.get('customer_message', 'Ok')]
                    
                    # Extract intent and strategy from LLM response
                    llm_intent = llm_response.get('intent', 'general_question')
                    llm_strategy = llm_response.get('strategy', action.get('action', 'answer_question'))
                    
                    latency_ms = int((time.time() - start_time) * 1000)
                except Exception as e:
                    print(f"Warning: LLM call failed: {e}, using fallback")
                    llm_messages = ["Ok"] if state['persona'] == 'ultra_short' else ["Entiendo, gracias"]
                    llm_intent = 'general_question'
                    llm_strategy = action.get('action', 'answer_question')
                    latency_ms = 0
                
                # Process each message: apply filters, imperfections, burst mode
                processed_messages = []
                all_filter_results = []
                
                for msg in llm_messages:
                    # Apply filters
                    filter_result = filter_message(
                        msg,
                        anchors,
                        max_length=MAX_MESSAGE_LENGTH
                    )
                    all_filter_results.append(filter_result)
                    
                    # Handle filtering failures
                    if filter_result['is_copying']:
                        print(f"Warning: Message too similar to anchor: {msg[:50]}...")
                    
                    filtered_msg = filter_result['filtered_message']
                    
                    # Ensure non-empty
                    if not filtered_msg.strip():
                        filtered_msg = "Ok" if state['persona'] == 'ultra_short' else "Entiendo"
                    
                    # Apply imperfections
                    filtered_msg = apply_imperfections(filtered_msg, state['persona'])
                    
                    # Render as burst messages (WhatsApp style)
                    msg_bursts = render_customer_messages(filtered_msg, state['persona'])
                    processed_messages.extend(msg_bursts)
                
                # Combine all processed messages for intent detection
                combined_for_intent = " ".join(processed_messages)
                
                # Use LLM-provided intent if available, otherwise detect
                if llm_intent and llm_intent != 'general_question':
                    detected_intent = llm_intent
                else:
                    customer_intent_result = detect_customer_intent(combined_for_intent, state['turns'][-6:])
                    detected_intent = customer_intent_result['intent']
                
                # Use processed messages as final output
                message_bursts = processed_messages
                filter_result = all_filter_results[0] if all_filter_results else {
                    'filtered_message': combined_for_intent,
                    'was_filtered': False,
                    'filters_applied': [],
                    'pii_found': [],
                    'is_copying': False,
                    'max_similarity': 0.0,
                    'content_valid': True,
                    'issues': []
                }
            
            # Update strategy from LLM response if available
            if 'llm_strategy' in locals():
                state['strategy'] = llm_strategy
            
            # Update last_customer_intents (rolling window of last 3)
            # Use combined message for intent tracking
            state['last_customer_intents'].append({
                'intent': detected_intent,
                'text': combined_for_intent,
                'turn_idx': state['turn_count']
            })
            if len(state['last_customer_intents']) > 3:
                state['last_customer_intents'].pop(0)
            
            # Store all bursts in state (use combined for turn tracking)
            state['turns'].append({
                'role': 'customer',
                'text': combined_for_intent,  # Combined for turn tracking
                'turn_idx': state['turn_count'],
                'action': action['action'],
                'metadata': {
                    'original_message': llm_messages[0] if 'llm_messages' in locals() and llm_messages else combined_for_intent,
                    'filter_result': filter_result,
                    'anchors_used': len(anchors),
                    'intent': detected_intent,
                    'message_bursts': message_bursts  # Store individual bursts
                }
            })
            state['turn_count'] += 1
            
            # Log turn
            turn_log = {
                "run_id": run_id,
                "turn_idx": state['turn_count'] - 1,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "role": "customer",
                "inputs": {
                    "dealership_message": dealership_message,
                    "scenario": state['scenario'],
                    "stage": state['stage'],
                    "persona": state['persona'],
                    "action": action,
                    "context": context,
                    "anchors": [
                        {
                            "customer_text": a.get('customer_text', ''),
                            "similarity": a.get('similarity_score', 0.0)
                        }
                        for a in anchors[:5]  # Log top 5
                    ],
                    "seed": seed,
                    "dealer_response_type": dealer_response_type,
                    "dealer_response_classification": dealer_response_classification
                },
                "output": {
                    "customer_message": combined_for_intent,
                    "customer_message_bursts": message_bursts,
                    "llm_messages": llm_messages if 'llm_messages' in locals() else [combined_for_intent],
                    "llm_intent": llm_intent if 'llm_intent' in locals() else detected_intent,
                    "llm_strategy": llm_strategy if 'llm_strategy' in locals() else state.get('strategy'),
                    "original_message": llm_messages[0] if 'llm_messages' in locals() and llm_messages else combined_for_intent,
                    "llm_model": "gpt-4o-mini",
                    "llm_temperature": 0.7
                },
                "filters": {
                    "was_filtered": filter_result['was_filtered'],
                    "filters_applied": filter_result['filters_applied'],
                    "pii_found": filter_result['pii_found'],
                    "is_copying": filter_result['is_copying'],
                    "max_similarity": filter_result['max_similarity'],
                    "content_valid": filter_result['content_valid'],
                    "issues": filter_result['issues']
                },
                "customer_state": {
                    "goal_intent": state['goal_intent'],
                    "attempts_same_goal": state['attempts_same_goal'],
                    "frustration": state['frustration'],
                    "patience": state['patience'],
                    "strategy": state['strategy']
                },
                "customer_intent": detected_intent,
                "strategy_switch_reason": action.get('strategy_switch_reason'),
                "metadata": {
                    "cost_usd": 0.0001,  # Approximate, would need token counting for accurate
                    "latency_ms": latency_ms,
                    "retry_count": 0
                }
            }
            
            try:
                log_turn(run_id, turn_log)
            except Exception as e:
                print(f"Warning: Logging failed: {e}")
            
            # Print customer response(s) with typing delay simulation
            print(f"\nCustomer:")
            for i, burst_msg in enumerate(message_bursts):
                print(f"  {burst_msg}")
                # Small delay between bursts (simulate typing)
                if i < len(message_bursts) - 1:
                    time.sleep(0.3)
            
            if state.get('debug_mode', False):
                print(f"[Debug: action={action['action']} | stage={state['stage']} | persona={state['persona']} | urgency={action['urgency']:.2f}]")
                if anchors:
                    print(f"[Anchors: {len(anchors)} retrieved, top similarity: {anchors[0].get('similarity_score', 0):.2f}]")
                if filter_result['was_filtered']:
                    print(f"[Filters: {', '.join(filter_result['filters_applied'])}]")
                if len(message_bursts) > 1:
                    print(f"[Burst mode: {len(message_bursts)} messages]")
            else:
                print(f"[{action['action']} | {state['stage']}]")
            
            print()
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Ending conversation.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            if state.get('debug_mode', False):
                traceback.print_exc()
            continue
    
    # Finalize run
    try:
        finalize_run(run_id, state)
        print(f"\nConversation saved to: {log_file}")
    except Exception as e:
        print(f"Warning: Failed to finalize run: {e}")
    
    print("\nGoodbye!")


if __name__ == "__main__":
    main()
