#!/usr/bin/env python3
"""
Step 4.3: Prompt Template
Build prompts for LLM customer simulation
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI  # type: ignore
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Load prompt template
PROMPT_TEMPLATE_FILE = Path(__file__).parent.parent / "docs" / "prompt_customer_simulator.txt"

# LLM configuration
LLM_MODEL = "gpt-4o-mini"  # Cost-effective, good for structured output
TEMPERATURE = 0.7  # Balance creativity and consistency


def load_prompt_template() -> str:
    """Load prompt template from file."""
    if not PROMPT_TEMPLATE_FILE.exists():
        raise FileNotFoundError(f"Prompt template not found: {PROMPT_TEMPLATE_FILE}")
    
    with open(PROMPT_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def separate_style_content_anchors(anchors: List[Dict], strategy: str = None, max_style: int = 4, max_content: int = 4) -> tuple[List[Dict], List[Dict]]:
    """
    Separate anchors into style anchors (tone) and content anchors (intent).
    
    Style anchors: Examples that show tone, brevity, WhatsApp style
    Content anchors: Examples that show similar intent/goal
    
    Args:
        anchors: List of anchor dicts
        strategy: Current strategy (to help prioritize content anchors)
        max_style: Maximum number of style anchors
        max_content: Maximum number of content anchors
    
    Returns:
        (style_anchors, content_anchors)
    """
    if not anchors:
        return [], []
    
    style_anchors = []
    content_anchors = []
    
    # Prioritize sentence_chunk for style (they're often good tone examples)
    # Prioritize customer_turn and dealer_customer_pair for content (they show intent)
    for anchor in anchors:
        snippet_type = anchor.get('snippet_type', 'customer_turn')
        customer_text = anchor.get('customer_text', '')
        
        # Style anchors: prefer sentence chunks, short messages, diverse tones
        if snippet_type == 'sentence_chunk' and len(style_anchors) < max_style:
            style_anchors.append(anchor)
        elif len(customer_text) < 100 and len(style_anchors) < max_style:
            # Short messages are good for style
            style_anchors.append(anchor)
        elif len(style_anchors) < max_style:
            # Fill remaining slots
            style_anchors.append(anchor)
    
    # Content anchors: prefer customer_turn and dealer_customer_pair
    for anchor in anchors:
        if anchor in style_anchors:
            continue
        
        snippet_type = anchor.get('snippet_type', 'customer_turn')
        
        if snippet_type in ['customer_turn', 'dealer_customer_pair'] and len(content_anchors) < max_content:
            content_anchors.append(anchor)
        elif len(content_anchors) < max_content:
            content_anchors.append(anchor)
    
    # Ensure we have some anchors even if separation wasn't perfect
    if not style_anchors and anchors:
        style_anchors = anchors[:max_style]
    if not content_anchors and anchors:
        remaining = [a for a in anchors if a not in style_anchors]
        content_anchors = remaining[:max_content]
    
    return style_anchors[:max_style], content_anchors[:max_content]


def format_style_anchors(anchors: List[Dict]) -> str:
    """Format style anchors for prompt."""
    if not anchors:
        return "No style examples available"
    
    examples = []
    examples.append("Style Examples (tone reference - use ONLY for tone/style, DO NOT copy):")
    for i, anchor in enumerate(anchors, 1):
        customer_text = anchor.get('customer_text', '')
        examples.append(f"  {i}. {customer_text}")
    
    return "\n".join(examples)


def format_content_anchors(anchors: List[Dict]) -> str:
    """Format content anchors for prompt."""
    if not anchors:
        return "No content examples available"
    
    examples = []
    examples.append("Content Examples (intent reference - use ONLY to understand goal/intent, DO NOT copy):")
    for i, anchor in enumerate(anchors, 1):
        customer_text = anchor.get('customer_text', '')
        examples.append(f"  {i}. {customer_text}")
    
    return "\n".join(examples)


def format_anchor_examples(anchors: List[Dict], max_examples: int = 8) -> str:
    """Format anchor examples for prompt (legacy function for backward compatibility)."""
    examples = []
    for i, anchor in enumerate(anchors[:max_examples], 1):
        customer_text = anchor.get('customer_text', '')
        examples.append(f"Example {i}: {customer_text}")
    
    return "\n".join(examples) if examples else "No examples available"


def format_conversation_context(turns: List[Dict], max_turns: int = 6) -> str:
    """Format conversation context from turns with flow indicators."""
    context_parts = []
    context_parts.append("Recent conversation flow:")
    
    for i, turn in enumerate(turns[-max_turns:], 1):
        role = turn.get('role', 'unknown')
        text = turn.get('text', '')
        turn_idx = turn.get('turn_idx', i)
        
        if role == 'dealership':
            context_parts.append(f"  Turn {turn_idx} - Dealership: {text}")
        elif role == 'customer':
            context_parts.append(f"  Turn {turn_idx} - Customer: {text}")
    
    if not context_parts or len(context_parts) == 1:
        return "No previous context"
    
    context_parts.append("\nNote: Pay attention to the conversation flow. If dealer acknowledges or confirms something, acknowledge back and move forward.")
    
    return "\n".join(context_parts)


def build_prompt(
    context: Dict,
    persona: Dict,
    scenario: str,
    stage: str,
    action: Dict,
    anchors: List[Dict],
    customer_state: Optional[Dict] = None
) -> str:
    """
    Build prompt for LLM customer simulation.
    
    Args:
        context: Dict with 'turns' list (last ~6 turns)
        persona: Persona dict with name, description, traits, style
        scenario: Current scenario
        stage: Current stage
        action: Action dict with 'action', 'reasoning'
        anchors: List of anchor snippets
        customer_state: Optional dict with goal_intent, attempts_same_goal, frustration, strategy
    
    Returns:
        Formatted prompt string
    """
    template = load_prompt_template()
    
    # Format conversation context
    turns = context.get('turns', [])
    conversation_context = format_conversation_context(turns, max_turns=6)
    
    # Format persona info
    persona_name = persona.get('name', 'Unknown')
    persona_description = persona.get('description', '')
    persona_traits = ', '.join(persona.get('traits', []))
    persona_style = json.dumps(persona.get('message_style', {}), indent=2, ensure_ascii=False)
    
    # Format customer state (with defaults)
    if customer_state:
        strategy = customer_state.get('strategy', action.get('action', 'answer_question'))
        goal_intent = customer_state.get('goal_intent', 'unknown')
        attempts_same_goal = customer_state.get('attempts_same_goal', 0)
        frustration = customer_state.get('frustration', 0.0)
    else:
        strategy = action.get('action', 'answer_question')
        goal_intent = 'unknown'
        attempts_same_goal = 0
        frustration = 0.0
    
    # Separate anchors into style and content
    style_anchors, content_anchors = separate_style_content_anchors(anchors, strategy=strategy)
    style_examples = format_style_anchors(style_anchors)
    content_examples = format_content_anchors(content_anchors)
    
    # Fill template
    prompt = template.format(
        conversation_context=conversation_context,
        persona_name=persona_name,
        persona_description=persona_description,
        persona_traits=persona_traits,
        persona_style=persona_style,
        scenario=scenario,
        stage=stage,
        action=action.get('action', 'answer_question'),
        action_reasoning=action.get('reasoning', ''),
        strategy=strategy,
        goal_intent=goal_intent,
        attempts_same_goal=attempts_same_goal,
        frustration=frustration,
        style_examples=style_examples,
        content_examples=content_examples
    )
    
    return prompt


def call_llm(prompt: str, max_retries: int = 3) -> Dict:
    """
    Call LLM with prompt and parse JSON response.
    
    Args:
        prompt: Full prompt string
        max_retries: Maximum retry attempts
    
    Returns:
        Parsed JSON dict with customer_message, action, confidence
    """
    if not OPENAI_AVAILABLE:
        raise ImportError("openai not installed. Install with: pip install openai")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = OpenAI(api_key=api_key)
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates realistic customer messages in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=TEMPERATURE,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                # Try to extract JSON from markdown code blocks
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                    result = json.loads(content)
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                    result = json.loads(content)
                else:
                    raise e
            
            # Handle new format (messages array) or old format (customer_message) for backward compatibility
            if 'messages' in result:
                # New format
                messages = result['messages']
                if not isinstance(messages, list) or len(messages) == 0:
                    raise ValueError("'messages' must be a non-empty array")
                
                # Validate messages are strings
                for i, msg in enumerate(messages):
                    if not isinstance(msg, str) or not msg.strip():
                        raise ValueError(f"Message {i} must be a non-empty string")
                
                # Validate required fields
                if 'intent' not in result:
                    raise ValueError("Missing 'intent' field in response")
                if 'strategy' not in result:
                    raise ValueError("Missing 'strategy' field in response")
                
                # Set defaults
                result.setdefault('confidence', 0.5)
                
                return result
            elif 'customer_message' in result:
                # Old format - convert to new format for backward compatibility
                customer_message = result.get('customer_message', 'Ok')
                return {
                    'messages': [customer_message],
                    'intent': result.get('intent', 'general_question'),
                    'strategy': result.get('strategy', result.get('action', 'answer_question')),
                    'confidence': result.get('confidence', 0.5)
                }
            else:
                raise ValueError("Response must contain either 'messages' array or 'customer_message' field")
        
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"Attempt {attempt + 1} failed: {e}, retrying...")
    
    raise RuntimeError("Failed to get valid response after retries")


def main():
    """Test prompt building and LLM call."""
    # Mock data for testing
    context = {
        "turns": [
            {"role": "dealership", "text": "¿Desea agendar una cita para el día de mañana?"},
            {"role": "customer", "text": "Para el Lunes podrá?"},
            {"role": "dealership", "text": "Claro, el día lunes tenemos disponibilidad..."}
        ]
    }
    
    persona = {
        "name": "Calm & Cooperative",
        "description": "Patient, helpful customer",
        "traits": ["polite", "patient", "cooperative"],
        "message_style": {"avg_length": "medium", "tone": "polite"}
    }
    
    action = {
        "action": "answer_question",
        "reasoning": "Dealership asked a question"
    }
    
    anchors = [
        {"customer_text": "Para el Lunes podrá?"},
        {"customer_text": "Ok muchas gracias"},
        {"customer_text": "Se lo comparto en un momento"}
    ]
    
    prompt = build_prompt(
        context=context,
        persona=persona,
        scenario="booking_service_appointment",
        stage="scheduling",
        action=action,
        anchors=anchors
    )
    
    print("Generated prompt:")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    
    # Uncomment to test LLM call (requires API key)
    # try:
    #     result = call_llm(prompt)
    #     print("\nLLM Response:")
    #     print(json.dumps(result, indent=2, ensure_ascii=False))
    # except Exception as e:
    #     print(f"\nLLM call failed: {e}")


if __name__ == "__main__":
    main()
