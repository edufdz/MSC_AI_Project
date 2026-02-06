#!/usr/bin/env python3
"""
Step 1.5: Role Detection
Classify each message as customer, dealership, or unknown using tiered approach
"""

import json
import re
from pathlib import Path
from typing import Dict, List

# Known dealership names/identifiers (Tier 1)
DEALERSHIP_NAMES = {
    'Chevrolet Calidad Tlahuac',
    'Chevrolet Tlahuac',
    'Citas Chevrolet Tlahuac',
    'Citas De Servicio Calidad Tlahuac',
    'Diana Anastasio',
    'system',  # System messages are usually from dealership
}

# Dealership signals (Tier 3 - Spanish)
DEALERSHIP_SIGNALS = [
    r'\ble atiende\b',
    r'\bmi nombre es\b',
    r'\bagencia\b',
    r'\bdistribuidor\b',
    r'\bcotización\b',
    r'\badjunto\b',
    r'\bconfirmo\b',
    r'\bdisponibilidad\b',
    r'\bhorarios? de recepción\b',
    r'\bestimado cliente\b',
    r'\bcon quien tengo el gusto\b',
    r'\bgracias por comunicarte\b',
    r'\basesor\b',
    r'\basesora\b',
    r'\bchevy\b',
    r'\bchevrolet\b',
    r'\bfolio\b',
    r'\bconfirmamos su cita\b',
    r'\bprogramar tu cita\b',
    r'\bservicio de mantenimiento\b',
]

# Customer signals (Tier 3 - Spanish)
CUSTOMER_SIGNALS = [
    r'\bmi coche\b',
    r'\bmi auto\b',
    r'\bmi unidad\b',
    r'\bmi vehículo\b',
    r'\bruido\b',
    r'\bfalla\b',
    r'\bproblema\b',
    r'\bno funciona\b',
    r'\bcuánto cuesta\b',
    r'\bcuánto tiempo\b',
    r'\bpuedo\b',
    r'\bme puede\b',
    r'\bme puede agendar\b',
    r'\bme puede dar\b',
    r'\burgente\b',
    r'\bno me han llamado\b',
    r'\bcuándo\b',
    r'\bquisiera\b',
    r'\bquiero\b',
    r'\bnecesito\b',
    r'\bmi número\b',
    r'\bmi teléfono\b',
    r'\bmi correo\b',
    r'\bmi email\b',
]

# Phone number pattern (Mexican format)
PHONE_PATTERN = re.compile(r'\+52\s?\d{2,3}\s?\d{3,4}\s?\d{4}')


def detect_role_tier1(speaker_raw: str) -> tuple[str, float]:
    """
    Tier 1: Metadata-based detection (highest confidence)
    Returns: (role, confidence)
    """
    speaker_lower = speaker_raw.lower().strip()
    
    # Check known dealership names
    for dealer_name in DEALERSHIP_NAMES:
        if dealer_name.lower() in speaker_lower:
            return ('dealership', 0.95)
    
    # Phone numbers starting with +52 are usually customers
    if PHONE_PATTERN.match(speaker_raw.strip()):
        return ('customer', 0.90)
    
    return (None, 0.0)


def detect_role_tier2(text: str) -> tuple[str, float]:
    """
    Tier 2: Speaker prefixes (if present)
    Returns: (role, confidence)
    """
    text_lower = text.lower()
    
    if re.search(r'\bcliente:\s*', text_lower):
        return ('customer', 0.85)
    if re.search(r'\basesor:\s*', text_lower) or re.search(r'\bagente:\s*', text_lower):
        return ('dealership', 0.85)
    
    return (None, 0.0)


def detect_role_tier3(text: str) -> tuple[str, float]:
    """
    Tier 3: Heuristic classifier (rules-based)
    Returns: (role, confidence)
    """
    text_lower = text.lower()
    
    dealership_score = 0
    customer_score = 0
    
    # Count dealership signals
    for signal in DEALERSHIP_SIGNALS:
        if re.search(signal, text_lower, re.IGNORECASE):
            dealership_score += 1
    
    # Count customer signals
    for signal in CUSTOMER_SIGNALS:
        if re.search(signal, text_lower, re.IGNORECASE):
            customer_score += 1
    
    # Calculate confidence based on score difference
    total_signals = dealership_score + customer_score
    if total_signals == 0:
        return (None, 0.0)
    
    score_diff = abs(dealership_score - customer_score)
    confidence = min(0.65 + (score_diff * 0.1), 0.90)  # Range: 0.65-0.90
    
    if dealership_score > customer_score:
        return ('dealership', confidence)
    elif customer_score > dealership_score:
        return ('customer', confidence)
    else:
        return (None, 0.0)


def detect_role(speaker_raw: str, text: str) -> tuple[str, float]:
    """
    Main role detection function using tiered approach.
    Returns: (role, confidence)
    """
    # Tier 1: Metadata
    role, confidence = detect_role_tier1(speaker_raw)
    if role:
        return (role, confidence)
    
    # Tier 2: Speaker prefixes
    role, confidence = detect_role_tier2(text)
    if role:
        return (role, confidence)
    
    # Tier 3: Heuristics
    role, confidence = detect_role_tier3(text)
    if role:
        return (role, confidence)
    
    # Tier 4: Default to unknown if confidence too low
    # (LLM fallback would go here, but skipping for now)
    return ('unknown', 0.5)


def main():
    """Main function to detect roles for all messages."""
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "out" / "parsed"
    
    # Find all JSON files
    json_files = sorted(input_dir.glob("*.json"))
    
    if not json_files:
        print(f"Warning: No JSON files found in {input_dir}")
        print("Run 04_normalize.py first!")
        return
    
    print(f"Detecting roles for {len(json_files)} conversations...")
    
    processed_count = 0
    role_counts = {'customer': 0, 'dealership': 0, 'unknown': 0}
    
    for json_file in json_files:
        try:
            # Load conversation
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            messages = data.get('messages', [])
            if not messages:
                continue
            
            # Detect role for each message
            for msg in messages:
                speaker_raw = msg.get('speaker_raw', '')
                text = msg.get('text', '') or msg.get('text_raw', '')
                
                role, confidence = detect_role(speaker_raw, text)
                
                msg['role'] = role
                msg['confidence'] = {'role': confidence}
                
                role_counts[role] += 1
            
            # Save updated JSON
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            processed_count += 1
            
            if processed_count % 20 == 0:
                print(f"  Processed {processed_count} conversations...")
        
        except Exception as e:
            print(f"  Error processing {json_file.name}: {e}")
            continue
    
    total_messages = sum(role_counts.values())
    unknown_rate = role_counts['unknown'] / total_messages if total_messages > 0 else 0
    
    print(f"\nSummary:")
    print(f"  Conversations processed: {processed_count}")
    print(f"  Total messages: {total_messages}")
    print(f"  Role distribution:")
    print(f"    Customer: {role_counts['customer']} ({role_counts['customer']/total_messages*100:.1f}%)")
    print(f"    Dealership: {role_counts['dealership']} ({role_counts['dealership']/total_messages*100:.1f}%)")
    print(f"    Unknown: {role_counts['unknown']} ({role_counts['unknown']/total_messages*100:.1f}%)")
    print(f"  Unknown rate: {unknown_rate*100:.1f}%")


if __name__ == "__main__":
    main()
