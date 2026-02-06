#!/usr/bin/env python3
"""
Step 3.1: Create Customer-Only Snippets
Extract customer turns with dealership context for retrieval
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

# PII patterns for validation
PII_PATTERNS = [
    re.compile(r'\+52\s?\d{2,3}\s?\d{3,4}\s?\d{4}'),  # Phone
    re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),  # Email
]


def has_pii(text: str) -> bool:
    """Check if text contains PII patterns."""
    if not text:
        return False
    for pattern in PII_PATTERNS:
        if pattern.search(text):
            return True
    return False


def load_labels(labels_file: Path) -> Dict[str, Dict]:
    """Load labels.jsonl and create lookup by conversation_id."""
    labels_dict = {}
    if not labels_file.exists():
        print(f"Warning: {labels_file} not found, proceeding without labels")
        return labels_dict
    
    with open(labels_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            label_data = json.loads(line)
            conv_id = label_data.get('conversation_id')
            if conv_id:
                labels_dict[conv_id] = label_data
    
    return labels_dict


def extract_snippets(conversations: List[Dict], labels_dict: Dict[str, Dict]) -> List[Dict]:
    """Extract customer snippets from conversations."""
    snippets = []
    
    for conv in conversations:
        conv_id = conv.get('conversation_id')
        turns = conv.get('turns', [])
        label_data = labels_dict.get(conv_id, {})
        stages = label_data.get('stages', [])
        scenario = label_data.get('scenario', 'unknown')
        
        # Track previous dealership turns
        prev_dealership_turns = []
        
        for turn_idx, turn in enumerate(turns):
            role = turn.get('role', 'unknown')
            text = turn.get('text', '').strip()
            
            # Skip empty text
            if not text:
                continue
            
            # Update previous dealership turns
            if role == 'dealership':
                prev_dealership_turns.append(text)
                # Keep only last 2 dealership turns
                if len(prev_dealership_turns) > 2:
                    prev_dealership_turns = prev_dealership_turns[-2:]
            
            # Extract customer snippets
            if role == 'customer':
                # Get stage for this turn
                stage = 'unknown'
                if stages and turn_idx < len(stages):
                    stage = stages[turn_idx]
                
                # Build prev_dealership_text
                prev_dealership_text = None
                if prev_dealership_turns:
                    prev_dealership_text = " | ".join(prev_dealership_turns)
                
                # Check for PII
                if has_pii(text) or (prev_dealership_text and has_pii(prev_dealership_text)):
                    print(f"Warning: PII detected in {conv_id} turn {turn_idx}, skipping")
                    continue
                
                # Create snippet
                snippet = {
                    'conversation_id': conv_id,
                    'turn_index': turn.get('turn_idx', turn_idx),
                    'customer_text': text,
                    'prev_dealership_text': prev_dealership_text,
                    'scenario': scenario,
                    'stage': stage,
                    'persona': None
                }
                
                snippets.append(snippet)
    
    return snippets


def main():
    """Main function to create customer snippets."""
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "out" / "dataset_post_sales_turns.json"
    labels_file = base_dir / "out" / "labels.jsonl"
    output_file = base_dir / "out" / "customer_snippets.jsonl"
    
    # Load dataset
    print(f"Loading dataset from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    conversations = dataset.get('conversations', [])
    print(f"Loaded {len(conversations)} conversations")
    
    # Load labels
    print(f"Loading labels from {labels_file}...")
    labels_dict = load_labels(labels_file)
    print(f"Loaded labels for {len(labels_dict)} conversations")
    
    # Extract snippets
    print("Extracting customer snippets...")
    snippets = extract_snippets(conversations, labels_dict)
    print(f"Extracted {len(snippets)} customer snippets")
    
    # Write JSONL file
    print(f"Writing snippets to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for snippet in snippets:
            f.write(json.dumps(snippet, ensure_ascii=False) + '\n')
    
    # Statistics
    scenarios = {}
    stages = {}
    for snippet in snippets:
        scenario = snippet.get('scenario', 'unknown')
        stage = snippet.get('stage', 'unknown')
        scenarios[scenario] = scenarios.get(scenario, 0) + 1
        stages[stage] = stages.get(stage, 0) + 1
    
    print(f"\n✅ Snippet extraction complete!")
    print(f"\nSummary:")
    print(f"  Total snippets: {len(snippets)}")
    print(f"  Snippets with context: {sum(1 for s in snippets if s.get('prev_dealership_text'))}")
    print(f"  Scenario distribution:")
    for scenario, count in sorted(scenarios.items()):
        print(f"    {scenario}: {count}")
    print(f"  Stage distribution:")
    for stage, count in sorted(stages.items(), key=lambda x: -x[1])[:10]:
        print(f"    {stage}: {count}")
    
    print(f"\nOutput file: {output_file}")


if __name__ == "__main__":
    main()
