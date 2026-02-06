#!/usr/bin/env python3
"""
Step 4.6: Message Variation
WhatsApp burst mode and controlled imperfections for realistic message generation
"""

import random
import re
from typing import List, Optional


# Burst mode probabilities by persona
BURST_MODE_PROBABILITIES = {
    "ultra_short": 0.1,
    "friendly_chatty": 0.6,
    "impatient_urgent": 0.4,
    "calm_cooperative": 0.2,
    "angry_escalating": 0.15,
    "confused_low_context": 0.25,
    "price_sensitive": 0.2,
    "need_it_today": 0.3
}

# Short greeting words that can start a burst
GREETING_WORDS = ["oye", "hola", "disculpa", "buen día", "buenas", "hey", "buenas tardes", "buenas noches"]

# Word shortening mappings (only if present in dataset)
WORD_SHORTENINGS = {
    "que": "q",
    "porque": "xq",
    "por qué": "xq",
    "donde": "dnd",
    "dónde": "dnd",
    "también": "tmb",
    "tambien": "tmb",
    "también": "tmb"
}

# Ack tokens by persona
ACK_TOKENS = {
    "ultra_short": ["va", "ok", "👍", "✅"],
    "friendly_chatty": ["va", "ok", "gracias", "👍", "😊"],
    "calm_cooperative": ["va", "ok", "gracias", "👍"],
    "impatient_urgent": ["ok", "va"],
    "angry_escalating": [],
    "confused_low_context": ["ok", "va"],
    "price_sensitive": ["ok", "gracias"],
    "need_it_today": ["ok", "va"]
}

# Emoji sets by persona
EMOJI_SETS = {
    "ultra_short": ["👍", "✅", "❌", "👌"],
    "friendly_chatty": ["😊", "👍", "✅", "👌", "🙏"],
    "calm_cooperative": ["👍", "✅"],
    "impatient_urgent": [],
    "angry_escalating": [],
    "confused_low_context": [],
    "price_sensitive": [],
    "need_it_today": []
}

# Emoji probabilities by persona
EMOJI_PROBABILITIES = {
    "ultra_short": 0.3,
    "friendly_chatty": 0.25,
    "calm_cooperative": 0.1,
    "impatient_urgent": 0.0,
    "angry_escalating": 0.0,
    "confused_low_context": 0.0,
    "price_sensitive": 0.0,
    "need_it_today": 0.05
}


def render_customer_messages(text: str, persona: str) -> List[str]:
    """
    Render customer message(s) with WhatsApp burst mode.
    
    Args:
        text: Original message text
        persona: Persona name
    
    Returns:
        List of message strings (1-3 messages)
    """
    if not text or not text.strip():
        return [text]
    
    text = text.strip()
    
    # Get burst probability for persona
    burst_prob = BURST_MODE_PROBABILITIES.get(persona, 0.2)
    
    # Decide if we should burst
    if random.random() > burst_prob:
        return [text]
    
    # Check if message is long enough to burst
    if len(text) < 30:
        return [text]
    
    # Split on natural breaks
    messages = _split_message(text, persona)
    
    # Limit to 3 messages max
    if len(messages) > 3:
        # Combine middle messages
        combined = " ".join(messages[1:-1])
        messages = [messages[0], combined, messages[-1]]
    
    return messages


def _split_message(text: str, persona: str) -> List[str]:
    """
    Split message on natural breaks.
    
    Args:
        text: Message text
        persona: Persona name
    
    Returns:
        List of message chunks
    """
    messages = []
    
    # Check if starts with greeting word
    first_chunk = None
    remaining_text = text
    
    for greeting in GREETING_WORDS:
        if text.lower().startswith(greeting.lower()):
            # Extract greeting
            greeting_len = len(greeting)
            if len(text) > greeting_len and text[greeting_len] in [' ', ',', ':']:
                first_chunk = greeting
                remaining_text = text[greeting_len:].strip()
                # Remove leading punctuation
                remaining_text = re.sub(r'^[,:\s]+', '', remaining_text)
                break
    
    # Split remaining text on natural breaks
    if remaining_text:
        # Prefer splitting on "del" first (common in Spanish: "del servicio", "del auto")
        # Then on other natural boundaries, but keep phrases like "más o menos" together
        words = remaining_text.split()
        
        # Find good split points (prefer "del" boundaries)
        split_indices = []
        for i, word in enumerate(words):
            # Split after "del" (creates natural boundary)
            if word.lower() == 'del' and i > 0:
                split_indices.append(i + 1)
            # Split before "más" if not part of "más o menos"
            elif word.lower() == 'más' and i > 0:
                # Check if next word is "o" (keep together)
                if i + 1 < len(words) and words[i + 1].lower() == 'o':
                    # Skip this split, keep "más o" together
                    continue
                else:
                    split_indices.append(i)
            # Split on commas (represented as separate words)
            elif word.endswith(',') and i > 0:
                split_indices.append(i + 1)
        
        # Create chunks based on split indices
        if split_indices:
            chunks = []
            start = 0
            for idx in split_indices:
                if idx > start:
                    chunk = " ".join(words[start:idx]).strip()
                    # Remove trailing commas
                    chunk = chunk.rstrip(',')
                    if chunk:
                        chunks.append(chunk)
                    start = idx
            
            # Add remaining words
            if start < len(words):
                chunk = " ".join(words[start:]).strip()
                if chunk:
                    chunks.append(chunk)
        else:
            # No good split points, try to split by length
            if len(words) > 6:
                # Split into roughly equal parts
                mid = len(words) // 2
                chunks = [
                    " ".join(words[:mid]),
                    " ".join(words[mid:])
                ]
            else:
                chunks = [remaining_text]
        
        # Combine chunks intelligently
        if first_chunk:
            messages.append(first_chunk)
        
        # Group chunks into 1-2 messages (max 3 total including greeting)
        if len(chunks) == 1:
            if first_chunk:
                messages.append(chunks[0])
            else:
                messages.append(chunks[0])
        elif len(chunks) == 2:
            messages.extend(chunks)
        else:
            # Split into 2 groups (to keep max 3 messages total)
            mid = len(chunks) // 2
            messages.append(" ".join(chunks[:mid]))
            messages.append(" ".join(chunks[mid:]))
    else:
        # Only greeting
        if first_chunk:
            messages.append(first_chunk)
    
    # Ensure minimum chunk size (except first chunk)
    min_chunk_size = 10
    final_messages = []
    for i, msg in enumerate(messages):
        if i == 0 and len(msg) < min_chunk_size and len(messages) > 1:
            # Combine with next message
            if i + 1 < len(messages):
                final_messages.append(msg + " " + messages[i + 1])
                # Skip next message
                messages[i + 1] = None
            else:
                final_messages.append(msg)
        elif msg and len(msg) >= min_chunk_size:
            final_messages.append(msg)
        elif msg:
            # Too short, combine with previous or next
            if final_messages:
                final_messages[-1] += " " + msg
            else:
                final_messages.append(msg)
    
    # Filter None values
    final_messages = [m for m in final_messages if m]
    
    # If no valid splits, return original
    if not final_messages:
        return [text]
    
    return final_messages


def apply_imperfections(text: str, persona: str, probability: float = 0.15) -> str:
    """
    Apply controlled imperfections to message.
    
    Args:
        text: Message text
        persona: Persona name
        probability: Base probability for imperfections
    
    Returns:
        Text with imperfections applied
    """
    if not text or not text.strip():
        return text
    
    result = text
    
    # 1. Shorten words (only for certain personas)
    if persona in ["ultra_short", "friendly_chatty"]:
        if random.random() < 0.05:
            result = _shorten_words(result)
    
    # 2. Remove punctuation (keep ? and !)
    if random.random() < 0.08:
        result = _remove_punctuation(result)
    
    # 3. Add ack tokens
    if random.random() < 0.1:
        result = _add_ack_tokens(result, persona)
    
    # 4. Emoji injection
    emoji_prob = EMOJI_PROBABILITIES.get(persona, 0.0)
    if random.random() < emoji_prob:
        result = _add_emoji(result, persona)
    
    return result


def _shorten_words(text: str) -> str:
    """Shorten common words."""
    result = text
    for full, short in WORD_SHORTENINGS.items():
        # Replace whole words only
        pattern = r'\b' + re.escape(full) + r'\b'
        if random.random() < 0.5:  # 50% chance per occurrence
            result = re.sub(pattern, short, result, flags=re.IGNORECASE)
    return result


def _remove_punctuation(text: str) -> str:
    """Remove trailing punctuation, keep ? and !"""
    # Remove trailing periods and commas
    result = re.sub(r'[,\.]+$', '', text)
    # Remove multiple spaces
    result = re.sub(r'\s+', ' ', result).strip()
    return result


def _add_ack_tokens(text: str, persona: str) -> str:
    """Add acknowledgment tokens."""
    ack_tokens = ACK_TOKENS.get(persona, [])
    if not ack_tokens:
        return text
    
    token = random.choice(ack_tokens)
    
    # Decide position: start (30%), end (60%), both (10%)
    rand = random.random()
    if rand < 0.3:
        return f"{token} {text}"
    elif rand < 0.9:
        return f"{text} {token}"
    else:
        return f"{token} {text} {token}"


def _add_emoji(text: str, persona: str) -> str:
    """Add emoji to message."""
    emoji_set = EMOJI_SETS.get(persona, [])
    if not emoji_set:
        return text
    
    emoji = random.choice(emoji_set)
    
    # Decide position: end (80%), start (15%), middle (5%)
    rand = random.random()
    if rand < 0.8:
        return f"{text} {emoji}"
    elif rand < 0.95:
        return f"{emoji} {text}"
    else:
        # Insert in middle (after first sentence or word)
        words = text.split()
        if len(words) > 3:
            mid = len(words) // 2
            return " ".join(words[:mid]) + f" {emoji} " + " ".join(words[mid:])
        else:
            return f"{text} {emoji}"


def main():
    """Test message variation functions."""
    test_messages = [
        "oye del servicio de 10k más o menos cuánto sale?",
        "Hola, quiero agendar una cita para el mantenimiento de mi auto",
        "Buen día, necesito saber si ya está listo mi vehículo",
        "Disculpa, tengo una pregunta sobre el precio",
        "Ok gracias",
    ]
    
    personas = ["friendly_chatty", "ultra_short", "calm_cooperative", "impatient_urgent"]
    
    print("Testing burst mode:\n")
    for persona in personas:
        print(f"\nPersona: {persona}")
        for msg in test_messages[:3]:
            bursts = render_customer_messages(msg, persona)
            print(f"  '{msg}'")
            print(f"  → {bursts}")
    
    print("\n\nTesting imperfections:\n")
    for persona in personas:
        print(f"\nPersona: {persona}")
        for msg in test_messages:
            imperfect = apply_imperfections(msg, persona)
            if imperfect != msg:
                print(f"  '{msg}'")
                print(f"  → '{imperfect}'")


if __name__ == "__main__":
    main()
