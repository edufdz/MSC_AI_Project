#!/usr/bin/env python3
"""
Step 4.5: Customer Intent Detection
Detect customer intent from messages and check for semantic repetition
"""

import re
from typing import Dict, List, Optional


# Intent patterns with keywords
INTENT_PATTERNS = {
    "price_quote": {
        "keywords": [
            r'\bcuánto cuesta\b',
            r'\bcuánto sale\b',
            r'\bcuánto vale\b',
            r'\bprecio\b',
            r'\bcosto\b',
            r'\bcuánto\b.*\bprecio\b',
            r'\bprecio\b.*\bcuánto\b',
            r'\bcuánto\b.*\bcuesta\b',
            r'\bcuánto\b.*\bsale\b',
            r'\bcuánto\b.*\bvale\b',
        ],
        "weight": 2.0
    },
    "book_appointment": {
        "keywords": [
            r'\bagendar\b',
            r'\bprogramar\b',
            r'\bcita\b',
            r'\bdisponibilidad\b',
            r'\bhorario\b',
            r'\bhorarios\b',
            r'\bdisponible\b',
            r'\bcuándo\b.*\bdisponible\b',
            r'\bdisponible\b.*\bcuándo\b',
            r'\bquiero agendar\b',
            r'\bnecesito cita\b',
            r'\bpuedo programar\b',
            r'\bquiero programar\b',
        ],
        "weight": 2.0
    },
    "status_update": {
        "keywords": [
            r'\bya está\b',
            r'\bya quedó\b',
            r'\bcuándo estará\b',
            r'\bpara cuándo\b',
            r'\bavance\b',
            r'\bstatus\b',
            r'\bestado\b',
            r'\bsigue en taller\b',
            r'\bcuándo puedo pasar\b',
            r'\bcuándo estará listo\b',
            r'\bya terminaron\b',
            r'\bestá listo\b',
        ],
        "weight": 2.0
    },
    "service_info": {
        "keywords": [
            r'\bqué incluye\b',
            r'\bqué servicio\b',
            r'\bmantenimiento\b',
            r'\bqué\b.*\bservicio\b',
            r'\bqu[ée]\b.*\bincluye\b',
            r'\bqu[ée]\b.*\bnecesita\b',
            r'\bqu[ée]\b.*\bhace\b',
            r'\bqu[ée]\b.*\brequiere\b',
        ],
        "weight": 1.5
    },
    "general_question": {
        "keywords": [
            r'\bqu[ée]\b',
            r'\bcómo\b',
            r'\bcuándo\b',
            r'\bdónde\b',
            r'\bpor qu[ée]\b',
            r'\bcuál\b',
        ],
        "weight": 0.5  # Lower weight as fallback
    }
}


def detect_customer_intent(customer_text: str, last_turns: Optional[List[Dict]] = None) -> Dict[str, any]:
    """
    Detect customer intent from message text.
    
    Args:
        customer_text: Customer message text
        last_turns: Optional list of recent turns for context
    
    Returns:
        {
            "intent": str,  # One of: price_quote, book_appointment, status_update, service_info, general_question
            "confidence": float (0.0-1.0)
        }
    """
    if not customer_text or not customer_text.strip():
        return {
            "intent": "general_question",
            "confidence": 0.1
        }
    
    text_lower = customer_text.lower().strip()
    
    intent_scores = {}
    
    # Score each intent
    for intent_name, intent_def in INTENT_PATTERNS.items():
        score = 0.0
        weight = intent_def.get("weight", 1.0)
        
        for pattern in intent_def["keywords"]:
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            if matches > 0:
                score += matches * weight
        
        if score > 0:
            intent_scores[intent_name] = score
    
    # If no intent detected, use general_question
    if not intent_scores:
        return {
            "intent": "general_question",
            "confidence": 0.3
        }
    
    # Find intent with highest score
    best_intent = max(intent_scores.items(), key=lambda x: x[1])
    intent_name = best_intent[0]
    intent_score = best_intent[1]
    
    # Calculate confidence (normalize score)
    max_possible_score = 10.0  # Rough estimate
    confidence = min(0.95, 0.4 + (intent_score / max_possible_score))
    
    return {
        "intent": intent_name,
        "confidence": confidence
    }


def is_semantic_repeat(intent1: str, intent2: str, text1: str, text2: str) -> bool:
    """
    Check if two customer messages are semantically similar (same intent + similar keywords).
    
    Args:
        intent1: Intent of first message
        intent2: Intent of second message
        text1: First message text
        text2: Second message text
    
    Returns:
        True if messages are semantically similar (repetition)
    """
    # If different intents, not a repeat
    if intent1 != intent2:
        return False
    
    # If same intent, check keyword overlap
    text1_lower = text1.lower()
    text2_lower = text2.lower()
    
    # Get keywords for this intent
    intent_patterns = INTENT_PATTERNS.get(intent1, {})
    keywords = intent_patterns.get("keywords", [])
    
    # Extract keywords from both texts
    text1_keywords = set()
    text2_keywords = set()
    
    for pattern in keywords:
        if re.search(pattern, text1_lower, re.IGNORECASE):
            # Extract the matched keyword
            match = re.search(pattern, text1_lower, re.IGNORECASE)
            if match:
                text1_keywords.add(match.group().lower())
        
        if re.search(pattern, text2_lower, re.IGNORECASE):
            match = re.search(pattern, text2_lower, re.IGNORECASE)
            if match:
                text2_keywords.add(match.group().lower())
    
    # If both texts share the same intent keywords, likely a repeat
    if text1_keywords and text2_keywords:
        overlap = text1_keywords.intersection(text2_keywords)
        if len(overlap) > 0:
            return True
    
    # Also check for very similar text (simple word overlap)
    words1 = set(re.findall(r'\b\w+\b', text1_lower))
    words2 = set(re.findall(r'\b\w+\b', text2_lower))
    
    # Remove common words
    common_words = {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'le', 'me', 'lo', 'los', 'las', 'con', 'por', 'para', 'su', 'sus', 'mi', 'mis', 'tu', 'tus', 'le', 'les'}
    words1 = words1 - common_words
    words2 = words2 - common_words
    
    if len(words1) > 0 and len(words2) > 0:
        overlap_ratio = len(words1.intersection(words2)) / min(len(words1), len(words2))
        # If more than 50% word overlap and same intent, likely a repeat
        if overlap_ratio > 0.5:
            return True
    
    return False


def get_intent_keywords(intent: str) -> List[str]:
    """
    Get keywords for a specific intent.
    
    Args:
        intent: Intent name
    
    Returns:
        List of keyword patterns
    """
    intent_def = INTENT_PATTERNS.get(intent, {})
    return intent_def.get("keywords", [])


def main():
    """Test intent detection."""
    test_cases = [
        ("¿Cuánto cuesta el servicio?", "price_quote"),
        ("Quiero agendar una cita", "book_appointment"),
        ("¿Ya está listo mi auto?", "status_update"),
        ("¿Qué incluye el mantenimiento?", "service_info"),
        ("¿Cuánto sale?", "price_quote"),
        ("Necesito programar una cita", "book_appointment"),
        ("¿Para cuándo estará?", "status_update"),
        ("¿Qué servicio necesito?", "service_info"),
        ("Hola", "general_question"),
        ("Ok gracias", "general_question"),
    ]
    
    print("Testing customer intent detection:\n")
    correct = 0
    total = len(test_cases)
    
    for text, expected_intent in test_cases:
        result = detect_customer_intent(text)
        predicted_intent = result["intent"]
        match = predicted_intent == expected_intent
        
        if match:
            correct += 1
            status = "✓"
        else:
            status = "✗"
        
        print(f"{status} Text: '{text}'")
        print(f"  Expected: {expected_intent}, Got: {predicted_intent} (confidence: {result['confidence']:.2f})")
        print()
    
    accuracy = (correct / total) * 100
    print(f"Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    
    # Test semantic repeat detection
    print("\nTesting semantic repeat detection:\n")
    repeat_tests = [
        ("¿Cuánto cuesta?", "¿Cuánto sale?", "price_quote", "price_quote", True),
        ("¿Cuánto cuesta?", "Quiero agendar", "price_quote", "book_appointment", False),
        ("¿Ya está listo?", "¿Para cuándo estará?", "status_update", "status_update", True),
        ("Hola", "Ok", "general_question", "general_question", False),  # Different general questions
    ]
    
    for text1, text2, intent1, intent2, expected in repeat_tests:
        result = is_semantic_repeat(intent1, intent2, text1, text2)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text1}' vs '{text2}'")
        print(f"  Expected: {expected}, Got: {result}")
        print()


if __name__ == "__main__":
    main()
