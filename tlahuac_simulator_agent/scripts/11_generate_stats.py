#!/usr/bin/env python3
"""
Step C: Generate Updated Stats
Calculate statistics for sanitized dataset
"""

import json
import statistics
import re
from pathlib import Path
from typing import Dict, List

# PII patterns for validation
PII_PATTERNS = {
    'PHONE': re.compile(r'\+52\s?\d{2,3}\s?\d{3,4}\s?\d{4}'),
    'EMAIL': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    'PLATE': re.compile(r'\b[A-Z]{3}-?\d{3,4}\b'),
    'VIN': re.compile(r'\b[A-HJ-NPR-Z0-9]{17}\b'),
    'NAME': re.compile(r'<NAME>'),
    'SURNAME': re.compile(r'<SURNAME>'),
}


def count_pii_in_text(text: str) -> Dict[str, int]:
    """Count PII placeholders in text."""
    counts = {}
    for pii_type, pattern in PII_PATTERNS.items():
        matches = len(pattern.findall(text))
        if matches > 0:
            counts[pii_type] = matches
    return counts


def calculate_stats(dataset: Dict) -> Dict:
    """Calculate comprehensive statistics for sanitized dataset."""
    conversations = dataset.get('conversations', [])
    total_conversations = len(conversations)
    
    # Message statistics
    all_messages = []
    post_sales_messages = []
    sales_messages = []
    
    # Role distribution
    role_counts = {'customer': 0, 'dealership': 0, 'unknown': 0, 'system': 0}
    
    # Topic distribution
    topic_counts = {'post_sales': 0, 'sales': 0, 'unknown': 0}
    
    # PII statistics
    pii_message_counts = {pii_type: 0 for pii_type in PII_PATTERNS.keys()}
    pii_total_messages = 0
    
    # System message tracking
    system_messages_removed = 0
    
    for conv in conversations:
        messages = conv.get('messages', [])
        all_messages.extend(messages)
        
        # Topic distribution
        labels = conv.get('labels', {})
        topic = labels.get('topic', 'unknown')
        topic_counts[topic] += 1
        
        # Filter messages by topic for separate stats
        if topic == 'post_sales':
            post_sales_messages.extend(messages)
        elif topic == 'sales':
            sales_messages.extend(messages)
        
        # Role distribution
        for msg in messages:
            role = msg.get('role', 'unknown')
            role_counts[role] += 1
            
            # PII detection
            text = msg.get('text', '')
            pii_in_msg = count_pii_in_text(text)
            if pii_in_msg:
                pii_total_messages += 1
                for pii_type, count in pii_in_msg.items():
                    pii_message_counts[pii_type] += count
    
    total_messages = len(all_messages)
    
    # Messages per conversation
    msg_counts = [len(conv.get('messages', [])) for conv in conversations]
    msg_counts_sorted = sorted(msg_counts)
    
    # Post-sales only stats
    post_sales_msg_counts = [len(conv.get('messages', [])) 
                             for conv in conversations 
                             if conv.get('labels', {}).get('topic') == 'post_sales']
    
    # Calculate unknown role rate (excluding system)
    non_system_messages = total_messages - role_counts.get('system', 0)
    unknown_rate = role_counts.get('unknown', 0) / non_system_messages if non_system_messages > 0 else 0
    
    # PII hit rates
    pii_hit_rates = {}
    for pii_type, count in pii_message_counts.items():
        pii_hit_rates[pii_type] = count / total_messages if total_messages > 0 else 0
    
    stats = {
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'system_messages_removed': system_messages_removed,  # Note: already removed in sanitized
        'messages_per_conversation': {
            'min': min(msg_counts) if msg_counts else 0,
            'max': max(msg_counts) if msg_counts else 0,
            'mean': statistics.mean(msg_counts) if msg_counts else 0,
            'median': statistics.median(msg_counts) if msg_counts else 0,
        },
        'role_distribution': {k: v for k, v in role_counts.items() if k != 'system'},
        'unknown_role_rate': unknown_rate,
        'topic_distribution': topic_counts,
        'post_sales_stats': {
            'conversations': topic_counts['post_sales'],
            'total_messages': len(post_sales_messages),
            'messages_per_conversation': {
                'min': min(post_sales_msg_counts) if post_sales_msg_counts else 0,
                'max': max(post_sales_msg_counts) if post_sales_msg_counts else 0,
                'mean': statistics.mean(post_sales_msg_counts) if post_sales_msg_counts else 0,
                'median': statistics.median(post_sales_msg_counts) if post_sales_msg_counts else 0,
            },
        },
        'sales_stats': {
            'conversations': topic_counts['sales'],
            'total_messages': len(sales_messages),
        },
        'pii_statistics': {
            'messages_with_pii': pii_total_messages,
            'pii_hit_rate': pii_total_messages / total_messages if total_messages > 0 else 0,
            'pii_by_type': pii_hit_rates,
            'pii_message_counts': pii_message_counts,
        },
        'language': 'es',
    }
    
    return stats


def main():
    """Main function to generate statistics."""
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "out" / "dataset_sanitized.json"
    output_file = base_dir / "out" / "stats_sanitized.json"
    
    if not input_file.exists():
        print(f"Error: {input_file} not found!")
        print("Run 10_label_topics.py first!")
        return
    
    print(f"Loading sanitized dataset from {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    print("Calculating statistics...")
    stats = calculate_stats(dataset)
    
    print(f"Writing statistics to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print("\n✅ Statistics generated!")
    print(f"\nSummary:")
    print(f"  Total conversations: {stats['total_conversations']}")
    print(f"  Total messages: {stats['total_messages']}")
    print(f"  Messages per conversation:")
    print(f"    Min: {stats['messages_per_conversation']['min']}")
    print(f"    Max: {stats['messages_per_conversation']['max']}")
    print(f"    Mean: {stats['messages_per_conversation']['mean']:.1f}")
    print(f"    Median: {stats['messages_per_conversation']['median']:.1f}")
    print(f"\n  Role distribution:")
    for role, count in stats['role_distribution'].items():
        pct = count / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
        print(f"    {role}: {count} ({pct:.1f}%)")
    print(f"  Unknown role rate: {stats['unknown_role_rate']*100:.1f}%")
    print(f"\n  Topic distribution:")
    for topic, count in stats['topic_distribution'].items():
        pct = count / stats['total_conversations'] * 100 if stats['total_conversations'] > 0 else 0
        print(f"    {topic}: {count} ({pct:.1f}%)")
    print(f"\n  Post-sales stats:")
    ps_stats = stats['post_sales_stats']
    print(f"    Conversations: {ps_stats['conversations']}")
    print(f"    Messages: {ps_stats['total_messages']}")
    print(f"    Avg messages/conversation: {ps_stats['messages_per_conversation']['mean']:.1f}")
    print(f"\n  PII statistics:")
    pii_stats = stats['pii_statistics']
    print(f"    Messages with PII: {pii_stats['messages_with_pii']}")
    print(f"    PII hit rate: {pii_stats['pii_hit_rate']*100:.1f}%")
    print(f"    PII by type:")
    for pii_type, rate in sorted(pii_stats['pii_by_type'].items()):
        count = pii_stats['pii_message_counts'].get(pii_type, 0)
        print(f"      {pii_type}: {count} occurrences ({rate*100:.1f}%)")
    
    print(f"\nStatistics saved to: {output_file}")


if __name__ == "__main__":
    main()
