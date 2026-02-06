#!/usr/bin/env python3
"""
Step A: Create Sanitized Dataset
Fix system messages, sanitize metadata, mask names/surnames
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set
from copy import deepcopy

# System message patterns
SYSTEM_MESSAGE_PATTERNS = [
    r'Los mensajes y las llamadas están cifrados',
    r'^-\s*$',  # Just "-"
    r'usa una duración predeterminada',  # Temporary messages notice
]

# Name detection triggers
NAME_TRIGGERS = [
    r'con quien tengo el gusto',
    r'con quién tengo el gusto',
    r'me brinda por favor su nombre',
    r'su nombre',
]

SURNAME_TRIGGERS = [
    r'me brinda por favor su apellido',
    r'su apellido',
]

# Phone number pattern for filename sanitization
PHONE_PATTERN = re.compile(r'\+52\s?\d{2,3}\s?\d{3,4}\s?\d{4}')


def is_system_message(msg: Dict) -> bool:
    """Check if message is a system message."""
    speaker = msg.get('speaker_raw', '')
    text = msg.get('text', '') or msg.get('text_raw', '')
    
    if speaker == 'system':
        return True
    
    for pattern in SYSTEM_MESSAGE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


def create_speaker_mapping(messages: List[Dict]) -> Dict[str, str]:
    """Create mapping from original speaker_raw to anonymized IDs."""
    mapping = {}
    customer_counter = 1
    dealership_counter = 1
    
    for msg in messages:
        speaker = msg.get('speaker_raw', '')
        role = msg.get('role', 'unknown')
        
        if not speaker or speaker in mapping:
            continue
        
        if speaker == 'system':
            mapping[speaker] = 'system'
        elif role == 'customer':
            mapping[speaker] = f'customer_{customer_counter}'
            customer_counter += 1
        elif role == 'dealership':
            mapping[speaker] = f'dealership_{dealership_counter}'
            dealership_counter += 1
        else:
            # Unknown role - try to infer from speaker pattern
            if PHONE_PATTERN.match(speaker.strip()):
                mapping[speaker] = f'customer_{customer_counter}'
                customer_counter += 1
            else:
                mapping[speaker] = f'dealership_{dealership_counter}'
                dealership_counter += 1
    
    return mapping


def sanitize_filename(filename: str, conv_id: str) -> str:
    """Remove phone numbers from filename."""
    # Remove phone number pattern
    sanitized = PHONE_PATTERN.sub('XXX', filename)
    # Simplify to just use conversation ID
    return f'chat_{conv_id}.txt'


def mask_names_in_conversation(messages: List[Dict]) -> List[Dict]:
    """Mask names and surnames using context-based rules."""
    pending_name = False
    pending_surname = False
    pii_types = set()
    
    for i, msg in enumerate(messages):
        text = msg.get('text', '')
        role = msg.get('role', 'unknown')
        
        # Check for triggers in dealership messages
        if role == 'dealership':
            text_lower = text.lower()
            for trigger in NAME_TRIGGERS:
                if re.search(trigger, text_lower):
                    pending_name = True
                    break
            
            for trigger in SURNAME_TRIGGERS:
                if re.search(trigger, text_lower):
                    pending_surname = True
                    break
        
        # Apply masking on next customer message
        if role == 'customer' and (pending_name or pending_surname):
            if pending_name:
                # Mask first word as <NAME>
                text = re.sub(r'^(\w+)', '<NAME>', text, count=1)
                pii_types.add('NAME')
                pending_name = False
            
            if pending_surname:
                # Mask entire message as <SURNAME>
                text = re.sub(r'^(.+)$', '<SURNAME>', text)
                pii_types.add('SURNAME')
                pending_surname = False
        
        # Pattern-based masking in dealership messages
        if role == 'dealership':
            # sr./sra. NAME
            original_text = text
            text = re.sub(r'\b(sr\.|sra\.)\s+([A-Z][a-z]+)', r'\1 <NAME>', text)
            if text != original_text:
                pii_types.add('NAME')
            
            # estimado NAME
            original_text = text
            text = re.sub(r'\bestimado\s+([A-Z][a-z]+)', r'estimado <NAME>', text, flags=re.IGNORECASE)
            if text != original_text:
                pii_types.add('NAME')
            
            # *NAME* *SURNAME* pattern (common in confirmation messages)
            original_text = text
            text = re.sub(r'\*([A-Z][A-Z\s]+)\*', lambda m: '*<NAME>*' if len(m.group(1).split()) == 1 else '*<NAME> <SURNAME>*', text)
            if text != original_text:
                pii_types.add('NAME')
                pii_types.add('SURNAME')
            
            # Full name patterns: NAME SURNAME (2-4 capitalized words)
            original_text = text
            text = re.sub(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:\s+[A-Z][a-z]+)?)\b', 
                         lambda m: '<NAME> <SURNAME>' if 2 <= len(m.group(1).split()) <= 4 else m.group(1), text)
            if text != original_text:
                pii_types.add('NAME')
                pii_types.add('SURNAME')
        
        # Update message
        msg['text'] = text
        
        # Update PII info if names were masked
        if pii_types:
            existing_pii = msg.get('pii', {})
            existing_types = set(existing_pii.get('types', []))
            existing_types.update(pii_types)
            msg['pii'] = {
                'has_pii': True,
                'types': sorted(list(existing_types))
            }
    
    return messages


def sanitize_conversation(conv: Dict) -> tuple[Dict, Dict]:
    """
    Sanitize a conversation.
    Returns: (sanitized_conversation, private_conversation)
    """
    # Deep copy for private version (keeps everything)
    private_conv = deepcopy(conv)
    
    # Start sanitized version
    sanitized_conv = deepcopy(conv)
    messages = sanitized_conv['messages']
    
    # Step 1: Fix system message roles and filter them
    system_messages = []
    non_system_messages = []
    
    for msg in messages:
        if is_system_message(msg):
            msg['role'] = 'system'
            system_messages.append(msg)
        else:
            non_system_messages.append(msg)
    
    # Step 2: Create speaker mapping
    speaker_mapping = create_speaker_mapping(messages)
    
    # Step 3: Apply speaker mapping and mask names
    sanitized_messages = []
    for msg in non_system_messages:
        # Map speaker_raw
        original_speaker = msg.get('speaker_raw', '')
        if original_speaker in speaker_mapping:
            msg['speaker_raw'] = speaker_mapping[original_speaker]
        
        # Remove text_raw from sanitized version
        if 'text_raw' in msg:
            del msg['text_raw']
        
        sanitized_messages.append(msg)
    
    # Step 4: Mask names in sanitized messages
    sanitized_messages = mask_names_in_conversation(sanitized_messages)
    
    # Step 5: Sanitize source.file
    conv_id = sanitized_conv.get('conversation_id', 'unknown')
    original_file = sanitized_conv['source']['file']
    sanitized_conv['source']['file'] = sanitize_filename(original_file, conv_id)
    
    # Update sanitized conversation
    sanitized_conv['messages'] = sanitized_messages
    
    return sanitized_conv, private_conv


def main():
    """Main function to create sanitized dataset."""
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "out" / "dataset.json"
    output_sanitized = base_dir / "out" / "dataset_sanitized.json"
    output_private = base_dir / "out" / "dataset_private.json"
    
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        print("Run 08_build_dataset.py first!")
        return
    
    print(f"Loading dataset from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    conversations = dataset.get('conversations', [])
    print(f"Processing {len(conversations)} conversations...")
    
    sanitized_conversations = []
    private_conversations = []
    
    total_messages_before = 0
    total_messages_after = 0
    system_messages_removed = 0
    
    for conv in conversations:
        total_messages_before += len(conv.get('messages', []))
        
        sanitized_conv, private_conv = sanitize_conversation(conv)
        
        system_count = len([m for m in conv.get('messages', []) if is_system_message(m)])
        system_messages_removed += system_count
        total_messages_after += len(sanitized_conv.get('messages', []))
        
        sanitized_conversations.append(sanitized_conv)
        private_conversations.append(private_conv)
    
    # Build sanitized dataset
    sanitized_dataset = {
        'dataset_version': 'v1_sanitized',
        'generated_at': dataset.get('generated_at'),
        'conversations': sanitized_conversations,
    }
    
    # Build private dataset
    private_dataset = {
        'dataset_version': 'v1_private',
        'generated_at': dataset.get('generated_at'),
        'conversations': private_conversations,
    }
    
    # Save sanitized dataset
    print(f"Writing sanitized dataset to {output_sanitized}...")
    with open(output_sanitized, 'w', encoding='utf-8') as f:
        json.dump(sanitized_dataset, f, ensure_ascii=False, indent=2)
    
    # Save private dataset
    print(f"Writing private dataset to {output_private}...")
    with open(output_private, 'w', encoding='utf-8') as f:
        json.dump(private_dataset, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Sanitization complete!")
    print(f"\nSummary:")
    print(f"  Total conversations: {len(conversations)}")
    print(f"  Messages before: {total_messages_before}")
    print(f"  Messages after: {total_messages_after}")
    print(f"  System messages removed: {system_messages_removed}")
    print(f"  Messages removed: {total_messages_before - total_messages_after}")


if __name__ == "__main__":
    main()
