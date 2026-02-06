#!/usr/bin/env python3
"""
Step 1.8: Build Unified Dataset
Combine all processed conversations into final JSON files
"""

import json
import statistics
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, List

def load_conversation(json_file: Path) -> Dict:
    """Load and transform a conversation JSON file into dataset format."""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract source file info
    source_file = data.get('source_file', json_file.name)
    
    # Transform messages to final format
    messages = []
    for msg in data.get('messages', []):
        message = {
            'idx': msg.get('idx'),
            'ts': msg.get('ts'),
            'speaker_raw': msg.get('speaker_raw', ''),
            'role': msg.get('role', 'unknown'),
            'text_raw': msg.get('text_raw', ''),
            'text': msg.get('text', ''),
            'pii': msg.get('pii', {'has_pii': False, 'types': []}),
            'confidence': msg.get('confidence', {'role': 0.5}),
        }
        messages.append(message)
    
    # Build conversation object
    conversation = {
        'conversation_id': '',  # Will be set later
        'source': {
            'system': 'whatsapp',
            'file': source_file,
        },
        'language': 'es',
        'messages': messages,
        'meta': {
            'dealer_id': None,
            'channel': 'whatsapp',
        }
    }
    
    return conversation


def calculate_stats(conversations: List[Dict]) -> Dict:
    """Calculate statistics for the dataset."""
    total_conversations = len(conversations)
    total_messages = sum(len(conv['messages']) for conv in conversations)
    
    # Messages per conversation
    msg_counts = [len(conv['messages']) for conv in conversations]
    msg_counts_sorted = sorted(msg_counts)
    
    # Role distribution
    role_counts = {'customer': 0, 'dealership': 0, 'unknown': 0}
    pii_counts = {}
    pii_total = 0
    
    for conv in conversations:
        for msg in conv['messages']:
            role = msg.get('role', 'unknown')
            role_counts[role] += 1
            
            # PII stats
            pii_info = msg.get('pii', {})
            if pii_info.get('has_pii', False):
                pii_total += 1
                for pii_type in pii_info.get('types', []):
                    pii_counts[pii_type] = pii_counts.get(pii_type, 0) + 1
    
    unknown_rate = role_counts['unknown'] / total_messages if total_messages > 0 else 0
    
    # PII hit rates
    pii_hit_rates = {}
    for pii_type, count in pii_counts.items():
        pii_hit_rates[pii_type] = count / total_messages if total_messages > 0 else 0
    
    stats = {
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'messages_per_conversation': {
            'min': min(msg_counts) if msg_counts else 0,
            'max': max(msg_counts) if msg_counts else 0,
            'mean': statistics.mean(msg_counts) if msg_counts else 0,
            'median': statistics.median(msg_counts) if msg_counts else 0,
        },
        'role_distribution': role_counts,
        'unknown_role_rate': unknown_rate,
        'pii_hit_rate': pii_hit_rates,
        'language': 'es',
    }
    
    return stats


def main():
    """Main function to build unified dataset."""
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "out" / "parsed"
    output_dir = base_dir / "out"
    
    # Find all JSON files
    json_files = sorted(input_dir.glob("*.json"))
    
    if not json_files:
        print(f"Warning: No JSON files found in {input_dir}")
        print("Run 07_validate.py first!")
        return
    
    print(f"Building dataset from {len(json_files)} conversations...")
    
    # Load all conversations
    conversations = []
    for json_file in json_files:
        try:
            conv = load_conversation(json_file)
            conversations.append(conv)
        except Exception as e:
            print(f"  Error loading {json_file.name}: {e}")
            continue
    
    # Assign conversation IDs
    for idx, conv in enumerate(conversations, 1):
        conv['conversation_id'] = f"conv_{idx:04d}"
    
    # Generate timestamp
    generated_at = datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Build dataset
    dataset = {
        'dataset_version': 'v1',
        'generated_at': generated_at,
        'conversations': conversations,
    }
    
    # Calculate statistics
    stats = calculate_stats(conversations)
    
    # Save full dataset
    dataset_file = output_dir / "dataset.json"
    print(f"Writing dataset.json ({len(conversations)} conversations)...")
    with open(dataset_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    # Save sample (first 5 conversations)
    sample_dataset = {
        'dataset_version': 'v1',
        'generated_at': generated_at,
        'conversations': conversations[:5],
    }
    sample_file = output_dir / "dataset.sample.json"
    print(f"Writing dataset.sample.json (5 conversations)...")
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(sample_dataset, f, ensure_ascii=False, indent=2)
    
    # Save statistics
    stats_file = output_dir / "stats.json"
    print(f"Writing stats.json...")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print(f"\n✅ Dataset built successfully!")
    print(f"\nSummary:")
    print(f"  Total conversations: {stats['total_conversations']}")
    print(f"  Total messages: {stats['total_messages']}")
    print(f"  Messages per conversation:")
    print(f"    Min: {stats['messages_per_conversation']['min']}")
    print(f"    Max: {stats['messages_per_conversation']['max']}")
    print(f"    Mean: {stats['messages_per_conversation']['mean']:.1f}")
    print(f"    Median: {stats['messages_per_conversation']['median']:.1f}")
    print(f"  Role distribution:")
    for role, count in stats['role_distribution'].items():
        pct = count / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
        print(f"    {role}: {count} ({pct:.1f}%)")
    print(f"  Unknown role rate: {stats['unknown_role_rate']*100:.1f}%")
    print(f"  PII hit rates:")
    for pii_type, rate in sorted(stats['pii_hit_rate'].items()):
        print(f"    {pii_type}: {rate*100:.1f}%")
    
    print(f"\nOutput files:")
    print(f"  {dataset_file}")
    print(f"  {sample_file}")
    print(f"  {stats_file}")


if __name__ == "__main__":
    main()
