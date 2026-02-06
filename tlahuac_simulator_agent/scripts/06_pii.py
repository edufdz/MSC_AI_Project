#!/usr/bin/env python3
"""
Step 1.6: PII Detection + Sanitization
Detect and replace PII with placeholders in text field (keep text_raw intact)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set

# PII Detection Patterns
PII_PATTERNS = {
    'PHONE': [
        re.compile(r'\+52\s?\d{2,3}\s?\d{3,4}\s?\d{4}'),  # +52 XXX XXX XXXX
        re.compile(r'\+52\d{10}'),  # +52XXXXXXXXXX
        re.compile(r'\(\d{3}\)\s?\d{3}-?\d{4}'),  # (XXX) XXX-XXXX
        re.compile(r'\d{3}-\d{3}-\d{4}'),  # XXX-XXX-XXXX
    ],
    'EMAIL': [
        re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    ],
    'PLATE': [
        re.compile(r'\b[A-Z]{3}-?\d{3,4}\b'),  # ABC-123 or ABC1234
        re.compile(r'\b[A-Z]{2}\s?[A-Z]?\s?\d{3,4}\b'),  # 32 BGV or AB 1234
        re.compile(r'\b\d{2}\s+[A-Z]{2,3}\b'),  # 32 BGV (Mexican format)
    ],
    'VIN': [
        re.compile(r'\b[A-HJ-NPR-Z0-9]{17}\b'),  # 17 alphanumeric (exclude I, O, Q)
    ],
    'ORDER_ID': [
        re.compile(r'\bFolio\s+(?:Cita|Cita:)?\s*:?\s*(\d{4,})', re.IGNORECASE),
        re.compile(r'\bfolio\s+(\d{4,})', re.IGNORECASE),
    ],
    'CASE_ID': [
        re.compile(r'\bCase\s+ID\s*:?\s*(\d+)', re.IGNORECASE),
        re.compile(r'\bTicket\s+(\d+)', re.IGNORECASE),
    ],
    'ADDRESS': [
        # Be conservative - only obvious addresses
        re.compile(r'\b(?:calle|avenida|av\.|colonia|col\.)\s+[A-Z0-9\s]+', re.IGNORECASE),
        re.compile(r'\bCDMX\b'),
        re.compile(r'\bIztapalapa\b'),
    ],
    # NAME is optional - skipping for now as it's too noisy
}


def sanitize_pii(text: str) -> tuple[str, Set[str]]:
    """
    Detect and replace PII with placeholders.
    Returns: (sanitized_text, pii_types_found)
    """
    sanitized = text
    pii_types_found = set()
    
    # Process in order: more specific patterns first
    for pii_type, patterns in PII_PATTERNS.items():
        for pattern in patterns:
            matches = list(pattern.finditer(sanitized))
            if matches:
                pii_types_found.add(pii_type)
                
                # Replace matches with placeholder (process in reverse to preserve indices)
                for match in reversed(matches):
                    start, end = match.span()
                    # For ORDER_ID and CASE_ID, we captured the number in group 1
                    if pii_type in ['ORDER_ID', 'CASE_ID'] and match.groups():
                        # Replace the whole match but keep context
                        sanitized = sanitized[:start] + f'<{pii_type}>' + sanitized[end:]
                    else:
                        sanitized = sanitized[:start] + f'<{pii_type}>' + sanitized[end:]
    
    return sanitized, pii_types_found


def main():
    """Main function to detect and sanitize PII."""
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "out" / "parsed"
    
    # Find all JSON files
    json_files = sorted(input_dir.glob("*.json"))
    
    if not json_files:
        print(f"Warning: No JSON files found in {input_dir}")
        print("Run 05_roles.py first!")
        return
    
    print(f"Detecting and sanitizing PII for {len(json_files)} conversations...")
    
    processed_count = 0
    pii_stats = {pii_type: 0 for pii_type in PII_PATTERNS.keys()}
    pii_stats['TOTAL'] = 0
    
    for json_file in json_files:
        try:
            # Load conversation
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            messages = data.get('messages', [])
            if not messages:
                continue
            
            # Process each message
            for msg in messages:
                text_raw = msg.get('text', '') or msg.get('text_raw', '')
                if not text_raw:
                    # Initialize PII fields
                    msg['pii'] = {'has_pii': False, 'types': []}
                    continue
                
                # Sanitize PII
                sanitized_text, pii_types = sanitize_pii(text_raw)
                
                # Update message
                msg['text'] = sanitized_text
                msg['pii'] = {
                    'has_pii': len(pii_types) > 0,
                    'types': sorted(list(pii_types))
                }
                
                # Update stats
                for pii_type in pii_types:
                    pii_stats[pii_type] += 1
                if pii_types:
                    pii_stats['TOTAL'] += 1
            
            # Save updated JSON
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            processed_count += 1
            
            if processed_count % 20 == 0:
                print(f"  Processed {processed_count} conversations...")
        
        except Exception as e:
            print(f"  Error processing {json_file.name}: {e}")
            continue
    
    total_messages = sum(len(json.load(open(f, 'r', encoding='utf-8')).get('messages', [])) 
                         for f in json_files)
    
    print(f"\nSummary:")
    print(f"  Conversations processed: {processed_count}")
    print(f"  Total messages: {total_messages}")
    print(f"  Messages with PII: {pii_stats['TOTAL']}")
    print(f"  PII by type:")
    for pii_type, count in sorted(pii_stats.items()):
        if pii_type != 'TOTAL':
            rate = count / total_messages if total_messages > 0 else 0
            print(f"    {pii_type}: {count} ({rate*100:.1f}%)")


if __name__ == "__main__":
    main()
