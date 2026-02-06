#!/usr/bin/env python3
"""
Step 2.1: Filter Post-Sales Conversations
Filter conversations where labels.topic == "post_sales"
"""

import json
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List

def calculate_stats(conversations: List[Dict]) -> Dict:
    """Calculate statistics for post-sales conversations."""
    total_conversations = len(conversations)
    
    # Message statistics
    all_messages = []
    for conv in conversations:
        all_messages.extend(conv.get('messages', []))
    
    total_messages = len(all_messages)
    msg_counts = [len(conv.get('messages', [])) for conv in conversations]
    
    # Role distribution
    role_counts = {'customer': 0, 'dealership': 0, 'unknown': 0}
    for msg in all_messages:
        role = msg.get('role', 'unknown')
        if role in role_counts:
            role_counts[role] += 1
    
    # PII statistics
    pii_counts = {}
    messages_with_pii = 0
    for msg in all_messages:
        pii_info = msg.get('pii', {})
        if pii_info.get('has_pii', False):
            messages_with_pii += 1
            for pii_type in pii_info.get('types', []):
                pii_counts[pii_type] = pii_counts.get(pii_type, 0) + 1
    
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
        'pii_statistics': {
            'messages_with_pii': messages_with_pii,
            'pii_hit_rate': messages_with_pii / total_messages if total_messages > 0 else 0,
            'pii_by_type': pii_counts,
        },
    }
    
    return stats

def main():
    """Main function to filter post-sales conversations."""
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "out" / "dataset_sanitized.json"
    output_file = base_dir / "out" / "dataset_post_sales.json"
    stats_file = base_dir / "out" / "stats_post_sales.json"
    
    # Load sanitized dataset
    print(f"Loading dataset from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    # Filter post-sales conversations
    all_conversations = dataset.get('conversations', [])
    post_sales_conversations = [
        conv for conv in all_conversations
        if conv.get('labels', {}).get('topic') == 'post_sales'
    ]
    
    print(f"Filtering post-sales conversations...")
    print(f"  Total conversations: {len(all_conversations)}")
    print(f"  Post-sales conversations: {len(post_sales_conversations)}")
    
    # Create filtered dataset
    filtered_dataset = {
        'dataset_version': 'v2_post_sales',
        'generated_at': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        'filter_criteria': {
            'topic': 'post_sales',
            'source_dataset': 'dataset_sanitized.json',
        },
        'conversations': post_sales_conversations,
    }
    
    # Calculate statistics
    stats = calculate_stats(post_sales_conversations)
    
    # Save filtered dataset
    print(f"Writing filtered dataset to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_dataset, f, ensure_ascii=False, indent=2)
    
    # Save statistics
    print(f"Writing statistics to {stats_file}...")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print(f"\n✅ Post-sales filtering complete!")
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
    print(f"  PII statistics:")
    print(f"    Messages with PII: {stats['pii_statistics']['messages_with_pii']}")
    print(f"    PII hit rate: {stats['pii_statistics']['pii_hit_rate']*100:.1f}%")
    print(f"    PII by type: {stats['pii_statistics']['pii_by_type']}")

if __name__ == "__main__":
    main()
