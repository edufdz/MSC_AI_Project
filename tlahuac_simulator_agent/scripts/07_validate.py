#!/usr/bin/env python3
"""
Step 1.7: Dataset Validation
Automated checks before final dataset generation
"""

import json
import re
from pathlib import Path
from typing import List, Dict

# PII patterns for validation (must NOT appear in sanitized text)
PII_VALIDATION_PATTERNS = {
    'PHONE': re.compile(r'\+52\s?\d{2,3}\s?\d{3,4}\s?\d{4}'),
    'EMAIL': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    'PLATE': re.compile(r'\b[A-Z]{3}-?\d{3,4}\b'),
    'VIN': re.compile(r'\b[A-HJ-NPR-Z0-9]{17}\b'),
}


def validate_conversation(conv_data: Dict, conv_id: str) -> List[str]:
    """
    Validate a single conversation.
    Returns list of error messages (empty if valid).
    """
    errors = []
    warnings = []
    
    messages = conv_data.get('messages', [])
    
    # Check 1: At least 2 messages
    if len(messages) < 2:
        errors.append(f"{conv_id}: Conversation has fewer than 2 messages ({len(messages)})")
    
    # Check 2: Message idx strictly increasing
    idxs = [msg.get('idx') for msg in messages]
    if idxs != list(range(len(messages))):
        errors.append(f"{conv_id}: Message idx not strictly increasing from 0")
    
    # Check 3: No duplicate idx values
    if len(idxs) != len(set(idxs)):
        errors.append(f"{conv_id}: Duplicate message idx values")
    
    # Check 4: Message content validation
    for msg in messages:
        msg_idx = msg.get('idx', -1)
        
        # text not empty
        text = msg.get('text', '')
        text_raw = msg.get('text_raw', '')
        
        if not text.strip():
            errors.append(f"{conv_id}[msg{msg_idx}]: text field is empty")
        
        if not text_raw.strip():
            errors.append(f"{conv_id}[msg{msg_idx}]: text_raw field is empty")
        
        # role in allowed set
        role = msg.get('role')
        if role not in ['customer', 'dealership', 'unknown']:
            errors.append(f"{conv_id}[msg{msg_idx}]: Invalid role '{role}'")
        
        # PII compliance: no real PII in sanitized text
        for pii_type, pattern in PII_VALIDATION_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{conv_id}[msg{msg_idx}]: Real {pii_type} found in sanitized text")
        
        # If pii.has_pii=True, text must contain placeholder
        pii_info = msg.get('pii', {})
        if pii_info.get('has_pii', False):
            pii_types = pii_info.get('types', [])
            for pii_type in pii_types:
                placeholder = f'<{pii_type}>'
                if placeholder not in text:
                    warnings.append(f"{conv_id}[msg{msg_idx}]: has_pii=True but placeholder <{pii_type}> not in text")
        
        # confidence.role in range [0.0, 1.0]
        confidence = msg.get('confidence', {})
        role_conf = confidence.get('role', 0.0)
        if not (0.0 <= role_conf <= 1.0):
            errors.append(f"{conv_id}[msg{msg_idx}]: confidence.role out of range: {role_conf}")
    
    # Check 5: Schema compliance
    if 'conversation_id' not in conv_data:
        errors.append(f"{conv_id}: Missing conversation_id")
    
    language = conv_data.get('language')
    if language != 'es':
        warnings.append(f"{conv_id}: language is '{language}', expected 'es'")
    
    # Check 6: Data quality
    roles = [msg.get('role') for msg in messages]
    unknown_count = roles.count('unknown')
    if unknown_count == len(roles):
        warnings.append(f"{conv_id}: All messages have unknown role")
    
    # Message length check
    for msg in messages:
        text = msg.get('text', '')
        if len(text) > 5000:
            warnings.append(f"{conv_id}[msg{msg.get('idx')}]: Very long message ({len(text)} chars)")
    
    return errors, warnings


def main():
    """Main function to validate all conversations."""
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "out" / "parsed"
    output_file = base_dir / "out" / "validation_report.json"
    
    # Find all JSON files
    json_files = sorted(input_dir.glob("*.json"))
    
    if not json_files:
        print(f"Warning: No JSON files found in {input_dir}")
        print("Run 06_pii.py first!")
        return
    
    print(f"Validating {len(json_files)} conversations...")
    
    all_errors = []
    all_warnings = []
    valid_count = 0
    total_messages = 0
    
    for json_file in json_files:
        try:
            # Load conversation
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Use filename as conversation ID for validation
            conv_id = json_file.stem
            
            errors, warnings = validate_conversation(data, conv_id)
            
            all_errors.extend(errors)
            all_warnings.extend(warnings)
            
            if not errors:
                valid_count += 1
            
            messages = data.get('messages', [])
            total_messages += len(messages)
        
        except Exception as e:
            all_errors.append(f"{json_file.name}: Error loading file - {e}")
    
    # Generate report
    report = {
        'valid': len(all_errors) == 0,
        'errors': all_errors,
        'warnings': all_warnings,
        'stats': {
            'total_conversations': len(json_files),
            'valid_conversations': valid_count,
            'failed_conversations': len(json_files) - valid_count,
            'total_messages': total_messages,
            'error_count': len(all_errors),
            'warning_count': len(all_warnings),
        }
    }
    
    # Save report
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print(f"\nValidation Summary:")
    print(f"  Total conversations: {len(json_files)}")
    print(f"  Valid conversations: {valid_count}")
    print(f"  Failed conversations: {len(json_files) - valid_count}")
    print(f"  Total messages: {total_messages}")
    print(f"  Errors: {len(all_errors)}")
    print(f"  Warnings: {len(all_warnings)}")
    
    if all_errors:
        print(f"\nFirst 10 errors:")
        for error in all_errors[:10]:
            print(f"  - {error}")
    
    if all_warnings and len(all_warnings) <= 20:
        print(f"\nWarnings:")
        for warning in all_warnings:
            print(f"  - {warning}")
    elif all_warnings:
        print(f"\nFirst 10 warnings:")
        for warning in all_warnings[:10]:
            print(f"  - {warning}")
    
    print(f"\nValidation report saved to: {output_file}")
    
    if not report['valid']:
        print("\n⚠️  Validation FAILED - fix errors before building dataset")
        return 1
    else:
        print("\n✅ Validation PASSED")
        return 0


if __name__ == "__main__":
    exit(main())
