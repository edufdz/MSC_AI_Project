#!/usr/bin/env python3
"""
Step 4.4: Hard Guardrails
Post-generation filters for PII, copying, length, and content validation
"""

import re
from typing import Dict, List, Optional
from difflib import SequenceMatcher

# PII patterns (same as Phase 1)
PII_PATTERNS = {
    'PHONE': [
        re.compile(r'\+52\s?\d{2,3}\s?\d{3,4}\s?\d{4}'),
        re.compile(r'\+52\d{10}'),
        re.compile(r'\(\d{3}\)\s?\d{3}-?\d{4}'),
        re.compile(r'\d{3}-\d{3}-\d{4}'),
    ],
    'EMAIL': [
        re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    ],
    'PLATE': [
        re.compile(r'\b[A-Z]{3}-?\d{3,4}\b'),
        re.compile(r'\b[A-Z]{2}\s?[A-Z]?\s?\d{3,4}\b'),
        re.compile(r'\b\d{2}\s+[A-Z]{2,3}\b'),
    ],
    'VIN': [
        re.compile(r'\b[A-HJ-NPR-Z0-9]{17}\b'),
    ],
}

# Dealership phrases to filter out
DEALERSHIP_PHRASES = [
    r'\ble atiende\b',
    r'\bestimado cliente\b',
    r'\bagencia\b',
    r'\bdistribuidor\b',
    r'\basesor\b',
    r'\basesora\b',
    r'\bgracias por comunicarte\b',
    r'\bcon quien tengo el gusto\b',
    r'\bconfirmamos su cita\b',
    r'\bprogramar tu cita\b',
    r'\bhorarios de recepción\b',
]


def scrub_pii(text: str) -> tuple[str, List[str]]:
    """
    Remove/replace PII with placeholders.
    
    Returns:
        (sanitized_text, pii_types_found)
    """
    sanitized = text
    pii_types_found = []
    
    for pii_type, patterns in PII_PATTERNS.items():
        for pattern in patterns:
            matches = list(pattern.finditer(sanitized))
            if matches:
                pii_types_found.append(pii_type)
                # Replace in reverse order to preserve indices
                for match in reversed(matches):
                    start, end = match.span()
                    placeholder = f'<{pii_type}>'
                    sanitized = sanitized[:start] + placeholder + sanitized[end:]
    
    return sanitized, pii_types_found


def check_copying(text: str, anchors: List[str], threshold: float = 0.8) -> tuple[bool, float]:
    """
    Check if text is too similar to any anchor (copying detection).
    
    Args:
        text: Generated message
        anchors: List of anchor texts to compare against
        threshold: Similarity threshold (default 0.8 = 80%)
    
    Returns:
        (is_copying, max_similarity)
    """
    if not anchors:
        return False, 0.0
    
    text_lower = text.lower().strip()
    max_similarity = 0.0
    
    for anchor in anchors:
        anchor_text = anchor.get('customer_text', '') if isinstance(anchor, dict) else str(anchor)
        anchor_lower = anchor_text.lower().strip()
        
        if not anchor_lower:
            continue
        
        # Calculate similarity using SequenceMatcher
        similarity = SequenceMatcher(None, text_lower, anchor_lower).ratio()
        max_similarity = max(max_similarity, similarity)
    
    is_copying = max_similarity >= threshold
    return is_copying, max_similarity


def cap_length(text: str, max_len: int = 240) -> tuple[str, bool]:
    """
    Truncate text to max length at word boundary.
    
    Returns:
        (truncated_text, was_truncated)
    """
    if len(text) <= max_len:
        return text, False
    
    # Truncate at word boundary
    truncated = text[:max_len]
    last_space = truncated.rfind(' ')
    if last_space > max_len * 0.8:  # Only truncate at word if we keep >80% of length
        truncated = truncated[:last_space]
    
    truncated = truncated.rstrip() + '...'
    return truncated, True


def validate_content(text: str) -> tuple[bool, List[str]]:
    """
    Validate content for dealership phrases, excessive punctuation, etc.
    
    Returns:
        (is_valid, issues)
    """
    issues = []
    
    # Check for dealership phrases
    text_lower = text.lower()
    for phrase_pattern in DEALERSHIP_PHRASES:
        if re.search(phrase_pattern, text_lower):
            issues.append(f"Contains dealership phrase: {phrase_pattern}")
    
    # Check for excessive punctuation
    if text.count('!') > 3 or text.count('?') > 3:
        issues.append("Excessive punctuation")
    
    # Check for excessive emojis (more than 3)
    emoji_count = len(re.findall(r'[😀-🙏🌀-🗿]', text))
    if emoji_count > 3:
        issues.append(f"Too many emojis ({emoji_count})")
    
    # Check if empty after stripping
    if not text.strip():
        issues.append("Empty message")
    
    return len(issues) == 0, issues


def filter_message(
    message: str,
    anchors: List[Dict],
    max_length: int = 240,
    copy_threshold: float = 0.8
) -> Dict[str, any]:
    """
    Apply all filters to generated message.
    
    Args:
        message: Generated customer message
        anchors: List of anchor snippets (for copying check)
        max_length: Maximum message length (default 240)
        copy_threshold: Similarity threshold for copying (default 0.8)
    
    Returns:
        {
            "filtered_message": "...",
            "was_filtered": True,
            "filters_applied": ["pii_scrub", "length_cap"],
            "original_length": 250,
            "final_length": 240,
            "pii_found": ["PHONE"],
            "is_copying": False,
            "max_similarity": 0.3,
            "content_valid": True,
            "issues": []
        }
    """
    original_length = len(message)
    filters_applied = []
    was_filtered = False
    
    # Step 1: PII scrub
    filtered_message, pii_found = scrub_pii(message)
    if pii_found:
        filters_applied.append("pii_scrub")
        was_filtered = True
    
    # Step 2: Anti-copy check
    anchor_texts = [a.get('customer_text', '') if isinstance(a, dict) else str(a) for a in anchors]
    is_copying, max_similarity = check_copying(filtered_message, anchor_texts, copy_threshold)
    
    # Step 3: Length cap
    filtered_message, was_truncated = cap_length(filtered_message, max_length)
    if was_truncated:
        filters_applied.append("length_cap")
        was_filtered = True
    
    # Step 4: Content validation
    content_valid, issues = validate_content(filtered_message)
    if issues:
        filters_applied.append("content_validation")
        was_filtered = True
    
    return {
        "filtered_message": filtered_message,
        "was_filtered": was_filtered,
        "filters_applied": filters_applied,
        "original_length": original_length,
        "final_length": len(filtered_message),
        "pii_found": pii_found,
        "is_copying": is_copying,
        "max_similarity": max_similarity,
        "content_valid": content_valid,
        "issues": issues
    }


def main():
    """Test filters."""
    # Test cases
    test_cases = [
        {
            "message": "Mi teléfono es +52 55 1234 5678",
            "anchors": [],
            "description": "PII in message"
        },
        {
            "message": "Para el Lunes podrá?",
            "anchors": [{"customer_text": "Para el Lunes podrá?"}],
            "description": "Exact copy"
        },
        {
            "message": "Este es un mensaje muy largo que debería ser truncado porque excede el límite de caracteres establecido para mensajes de WhatsApp que es de 240 caracteres aproximadamente y este mensaje tiene más que eso.",
            "anchors": [],
            "description": "Too long"
        },
        {
            "message": "Le atiende el asesor",
            "anchors": [],
            "description": "Dealership phrase"
        }
    ]
    
    print("Testing filters:\n")
    for i, test in enumerate(test_cases, 1):
        result = filter_message(test["message"], test["anchors"])
        print(f"Test {i}: {test['description']}")
        print(f"  Original: {test['message'][:60]}...")
        print(f"  Filtered: {result['filtered_message'][:60]}...")
        print(f"  Filters applied: {result['filters_applied']}")
        print(f"  PII found: {result['pii_found']}")
        print(f"  Is copying: {result['is_copying']} (similarity: {result['max_similarity']:.2f})")
        print(f"  Content valid: {result['content_valid']}")
        if result['issues']:
            print(f"  Issues: {result['issues']}")
        print()


if __name__ == "__main__":
    main()
