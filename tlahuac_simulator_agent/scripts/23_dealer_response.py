#!/usr/bin/env python3
"""
Step 4.4: Dealer Response Classification
Classify dealership messages as helpful, uncertain, blocking, or rude/low-effort
"""

import re
from typing import Dict, List


# Helpful signals - dealership is providing information or taking action
HELPFUL_SIGNALS = [
    r'\bpregunta\b',
    r'\bprecio\b',
    r'\bcosto\b',
    r'\bhorario\b',
    r'\bhorarios\b',
    r'\bdisponible\b',
    r'\bdisponibilidad\b',
    r'\bagendar\b',
    r'\bprogramar\b',
    r'\bcita\b',
    r'\bpaso\b',
    r'\binformación\b',
    r'\binfo\b',
    r'\bte puedo\b',
    r'\ble puedo\b',
    r'\bte ayudo\b',
    r'\ble ayudo\b',
    r'\bclaro\b',
    r'\bpor supuesto\b',
    r'\bsí\b',
    r'\bperfecto\b',
    r'\bexcelente\b',
    r'\bmodelo\b',
    r'\baño\b',
    r'\bkilometraje\b',
    r'\bkm\b',
    r'\bservicio\b',
    r'\bmantenimiento\b',
    r'\bcuánto\b',
    r'\bcuando\b',
    r'\bcuándo\b',
    r'\bqué\b',
    r'\bcómo\b',
    r'\bdónde\b',
    # Explanatory phrases (helpful explanations)
    r'\bes para\b',
    r'\bpara identificar\b',
    r'\bpara verificar\b',
    r'\bpara buscar\b',
    r'\bpara consultar\b',
    r'\bpara revisar\b',
    r'\ben la base de datos\b',
    r'\bte explico\b',
    r'\ble explico\b',
    r'\bte digo\b',
    r'\ble digo\b',
    r'\bnecesitamos\b',
    r'\bnecesito\b',
    r'\brequerimos\b',
    r'\brequiere\b',
    r'\bcon el fin de\b',
    r'\bcon la finalidad de\b',
]

# Uncertain signals - dealership doesn't know or needs to check
UNCERTAIN_SIGNALS = [
    r'\bno sé\b',
    r'\bno tengo\b',
    r'\bno estoy seguro\b',
    r'\bno estoy segura\b',
    r'\bdéjame revisar\b',
    r'\bdejame revisar\b',
    r'\bdéjame verificar\b',
    r'\bdejame verificar\b',
    r'\bni idea\b',
    r'\bverificar\b',
    r'\brevisar\b',
    r'\bconsultar\b',
    r'\bno tengo esa información\b',
    r'\bno tengo la información\b',
    r'\bno tengo el dato\b',
    r'\bno tengo los datos\b',
    r'\bno manejo esa información\b',
    r'\bno tengo acceso\b',
    r'\bno puedo ver\b',
    r'\bno puedo consultar\b',
]

# Blocking signals - dealership cannot help or is closed/unavailable
BLOCKING_SIGNALS = [
    r'\bcerrado\b',
    r'\bcerrados\b',
    r'\bestamos cerrados\b',
    r'\bestá cerrado\b',
    r'\bno atendemos\b',
    r'\bno hay sistema\b',
    r'\bno hacemos\b',
    r'\bno hacemos eso\b',
    r'\bfuera de zona\b',
    r'\bno disponible\b',
    r'\bno tenemos\b',
    r'\bno ofrecemos\b',
    r'\bno manejamos\b',
    r'\bno trabajamos\b',
    r'\bno podemos\b',
    r'\bno se puede\b',
    r'\bno está disponible\b',
    r'\bno hay disponibilidad\b',
    r'\bno hay citas\b',
    r'\bno hay horarios\b',
    r'\bno hay turnos\b',
    r'\bno hay servicio\b',
    r'\bno hay personal\b',
    r'\bno hay técnico\b',
    r'\bno hay mecánico\b',
]

# Rude/low-effort signals - very short dismissive responses
RUDE_SIGNALS = [
    r'^no$',
    r'^nope$',
    r'^ajá$',
    r'^aja$',
    r'^pues no$',
    r'^pues no\.$',
    r'^no\.$',
    r'^no,$',
    r'^no\s*$',
]

# Acknowledgment signals - dealer acknowledging/agreeing (context-dependent)
ACKNOWLEDGMENT_SIGNALS = [
    r'^ok$',
    r'^ok\.$',
    r'^ok,$',
    r'^ok\s*$',
    r'^claro$',
    r'^claro\.$',
    r'^sí$',
    r'^si$',
    r'^perfecto$',
    r'^va$',
    r'^listo$',
]


def classify_dealer_response(dealer_text: str, previous_customer_turn: str = None) -> Dict[str, any]:
    """
    Classify dealership response type.
    
    Args:
        dealer_text: Dealership message text
        previous_customer_turn: Previous customer message (for context)
    
    Returns:
        {
            "type": "helpful" | "uncertain" | "blocking" | "rude",
            "confidence": float (0.0-1.0),
            "signals": List[str]  # Matched signals
        }
    """
    if not dealer_text or not dealer_text.strip():
        return {
            "type": "uncertain",
            "confidence": 0.5,
            "signals": []
        }
    
    text_lower = dealer_text.lower().strip()
    text_length = len(text_lower)
    
    signals_found = []
    scores = {
        "helpful": 0,
        "uncertain": 0,
        "blocking": 0,
        "rude": 0
    }
    
    # Check for acknowledgment signals (context-dependent)
    # If customer just threatened to leave or asked for confirmation, "ok" is helpful acknowledgment
    is_acknowledgment_context = False
    if previous_customer_turn:
        prev_lower = previous_customer_turn.lower()
        if any(phrase in prev_lower for phrase in ['buscar otra', 'otra opción', 'otro lugar', 'tendré que', 'me voy', 'me iré', 'necesito', 'urgente', 'confirmar', 'asegurar']):
            is_acknowledgment_context = True
    
    # Check for acknowledgment first (if in context)
    if text_length < 15 and is_acknowledgment_context:
        for pattern in ACKNOWLEDGMENT_SIGNALS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                # In acknowledgment context, this is helpful
                scores["helpful"] += 3
                signals_found.append(f"helpful:acknowledgment:{pattern}")
                return {
                    "type": "helpful",
                    "confidence": 0.8,
                    "signals": signals_found
                }
    
    # Check for rude/low-effort (short dismissive responses, but not acknowledgments)
    if text_length < 15:  # Very short message
        for pattern in RUDE_SIGNALS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                scores["rude"] += 3
                signals_found.append(f"rude:{pattern}")
                break
    
    # Check helpful signals
    for pattern in HELPFUL_SIGNALS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            scores["helpful"] += 1
            signals_found.append(f"helpful:{pattern}")
    
    # Check uncertain signals
    for pattern in UNCERTAIN_SIGNALS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            scores["uncertain"] += 2  # Weight uncertain higher
            signals_found.append(f"uncertain:{pattern}")
    
    # Check blocking signals
    for pattern in BLOCKING_SIGNALS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            scores["blocking"] += 2  # Weight blocking higher
            signals_found.append(f"blocking:{pattern}")
    
    # Determine type based on highest score
    max_score = max(scores.values())
    
    if max_score == 0:
        # No signals found - default to helpful if message is substantial
        if text_length > 20:
            return {
                "type": "helpful",
                "confidence": 0.3,
                "signals": []
            }
        else:
            return {
                "type": "uncertain",
                "confidence": 0.4,
                "signals": []
            }
    
    # Find type with highest score
    if scores["rude"] > 0 and scores["rude"] >= max_score:
        response_type = "rude"
        confidence = min(0.9, 0.5 + (scores["rude"] / 10))
    elif scores["blocking"] >= max_score:
        response_type = "blocking"
        confidence = min(0.95, 0.6 + (scores["blocking"] / 10))
    elif scores["uncertain"] >= max_score:
        response_type = "uncertain"
        confidence = min(0.9, 0.5 + (scores["uncertain"] / 10))
    elif scores["helpful"] >= max_score:
        response_type = "helpful"
        confidence = min(0.9, 0.5 + (scores["helpful"] / 15))
    else:
        # Fallback
        response_type = "helpful"
        confidence = 0.5
    
    return {
        "type": response_type,
        "confidence": confidence,
        "signals": signals_found
    }


def main():
    """Test the classifier."""
    test_cases = [
        ("¿Qué modelo es tu vehículo?", "helpful"),
        ("No sé, déjame revisar", "uncertain"),
        ("No sé el precio exacto", "uncertain"),
        ("Estamos cerrados los domingos", "blocking"),
        ("No atendemos esa zona", "blocking"),
        ("No hay sistema disponible", "blocking"),
        ("No", "rude"),
        ("Ajá", "rude"),
        ("Pues no", "rude"),
        ("Claro, te puedo ayudar con eso", "helpful"),
        ("El precio es $2000", "helpful"),
        ("Déjame verificar la disponibilidad", "uncertain"),
        ("No tengo esa información a la mano", "uncertain"),
        ("No hacemos ese tipo de servicio", "blocking"),
        ("Ok", "rude"),  # Very short, low effort
    ]
    
    print("Testing dealer response classifier:\n")
    correct = 0
    total = len(test_cases)
    
    for text, expected_type in test_cases:
        result = classify_dealer_response(text)
        predicted_type = result["type"]
        match = predicted_type == expected_type
        
        if match:
            correct += 1
            status = "✓"
        else:
            status = "✗"
        
        print(f"{status} Text: '{text}'")
        print(f"  Expected: {expected_type}, Got: {predicted_type} (confidence: {result['confidence']:.2f})")
        print(f"  Signals: {result['signals'][:3]}")  # Show first 3 signals
        print()
    
    accuracy = (correct / total) * 100
    print(f"Accuracy: {correct}/{total} ({accuracy:.1f}%)")


if __name__ == "__main__":
    main()
