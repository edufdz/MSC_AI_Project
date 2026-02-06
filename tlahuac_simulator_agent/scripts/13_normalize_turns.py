#!/usr/bin/env python3
"""
Step 2.2: Normalize Turns
Group consecutive messages by same role into turns
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def normalize_turns(messages: List[Dict]) -> List[Dict]:
    """
    Group consecutive messages by same role into turns.
    Returns list of turn objects.
    """
    if not messages:
        return []
    
    turns = []
    current_turn = None
    
    for msg in messages:
        role = msg.get('role', 'unknown')
        text = msg.get('text', '').strip()
        msg_idx = msg.get('idx', -1)
        
        # Skip empty messages
        if not text:
            continue
        
        # Start new turn if role changes or first message
        if current_turn is None or current_turn['role'] != role:
            # Save previous turn if exists
            if current_turn is not None:
                turns.append(current_turn)
            
            # Start new turn
            current_turn = {
                'turn_idx': len(turns),
                'role': role,
                'text': text,
                'message_indices': [msg_idx],
                'message_count': 1
            }
        else:
            # Continue current turn - append text
            current_turn['text'] += ' ' + text
            current_turn['message_indices'].append(msg_idx)
            current_turn['message_count'] += 1
    
    # Don't forget the last turn
    if current_turn is not None:
        turns.append(current_turn)
    
    return turns


def main():
    """Main function to normalize turns for all conversations."""
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "out" / "dataset_post_sales.json"
    output_file = base_dir / "out" / "dataset_post_sales_turns.json"
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        print("Run 12_filter_post_sales.py first!")
        return
    
    print(f"Loading post-sales dataset from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    conversations = dataset.get('conversations', [])
    print(f"Normalizing turns for {len(conversations)} conversations...")
    
    total_messages_before = 0
    total_turns_after = 0
    reduction_stats = []
    
    for conv in conversations:
        messages = conv.get('messages', [])
        total_messages_before += len(messages)
        
        # Normalize turns
        turns = normalize_turns(messages)
        conv['turns'] = turns
        total_turns_after += len(turns)
        
        # Track reduction
        if len(messages) > 0:
            reduction = (len(messages) - len(turns)) / len(messages) * 100
            reduction_stats.append(reduction)
    
    # Update dataset metadata
    dataset['dataset_version'] = 'v2_post_sales_turns'
    dataset['generated_at'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Save output
    print(f"Writing normalized dataset to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    # Print summary
    avg_reduction = sum(reduction_stats) / len(reduction_stats) if reduction_stats else 0
    
    print(f"\n✅ Turn normalization complete!")
    print(f"\nSummary:")
    print(f"  Total conversations: {len(conversations)}")
    print(f"  Messages before: {total_messages_before}")
    print(f"  Turns after: {total_turns_after}")
    print(f"  Average reduction: {avg_reduction:.1f}%")
    print(f"  Messages per conversation (before): {total_messages_before / len(conversations):.1f}")
    print(f"  Turns per conversation (after): {total_turns_after / len(conversations):.1f}")


if __name__ == "__main__":
    main()
