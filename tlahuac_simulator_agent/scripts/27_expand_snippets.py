#!/usr/bin/env python3
"""
Step 3.3: Expand Snippets 10x
Create multiple retrieval units per conversation for better diversity
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


def split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    if not text:
        return []
    
    # Split on sentence boundaries (period, question mark, exclamation)
    sentences = re.split(r'([.!?]+)', text)
    
    # Combine sentences with their punctuation
    result = []
    i = 0
    while i < len(sentences):
        sentence = sentences[i].strip()
        if sentence:
            # Check if next item is punctuation
            if i + 1 < len(sentences) and sentences[i + 1] in ['.', '!', '?', '...']:
                sentence += sentences[i + 1]
                i += 2
            else:
                i += 1
            
            if sentence:
                result.append(sentence)
        else:
            i += 1
    
    # Fallback: if no sentence boundaries found, return as single sentence
    if not result:
        return [text]
    
    return result


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


def expand_snippets(conversations: List[Dict], labels_dict: Dict[str, Dict]) -> List[Dict]:
    """
    Expand snippets by creating multiple retrieval units per conversation.
    
    Creates:
    1. Customer turn alone (existing)
    2. Dealer+Customer pair
    3. 3-turn window (sliding)
    4. Sentence chunks (from customer messages)
    """
    snippets = []
    
    for conv in conversations:
        conv_id = conv.get('conversation_id')
        turns = conv.get('turns', [])
        label_data = labels_dict.get(conv_id, {})
        stages = label_data.get('stages', [])
        scenario = label_data.get('scenario', 'unknown')
        
        # Track previous turns for context
        prev_turns = []  # Last 3 turns (any role)
        prev_dealership_turns = []  # Last 2 dealership turns
        
        for turn_idx, turn in enumerate(turns):
            role = turn.get('role', 'unknown')
            text = turn.get('text', '').strip()
            
            # Skip empty text
            if not text:
                continue
            
            # Update previous turns tracking
            if role == 'dealership':
                prev_dealership_turns.append(text)
                if len(prev_dealership_turns) > 2:
                    prev_dealership_turns = prev_dealership_turns[-2:]
            
            # Update sliding window
            prev_turns.append({'role': role, 'text': text})
            if len(prev_turns) > 3:
                prev_turns = prev_turns[-3:]
            
            # Get stage for this turn
            stage = 'unknown'
            if stages and turn_idx < len(stages):
                stage = stages[turn_idx]
            
            # Extract customer snippets
            if role == 'customer':
                # Check for PII
                if has_pii(text):
                    print(f"Warning: PII detected in {conv_id} turn {turn_idx}, skipping")
                    continue
                
                # Build prev_dealership_text
                prev_dealership_text = None
                if prev_dealership_turns:
                    prev_dealership_text = " | ".join(prev_dealership_turns)
                
                # 1. Customer turn alone (existing type)
                snippet = {
                    'conversation_id': conv_id,
                    'turn_index': turn.get('turn_idx', turn_idx),
                    'customer_text': text,
                    'prev_dealership_text': prev_dealership_text,
                    'scenario': scenario,
                    'stage': stage,
                    'persona': None,
                    'snippet_type': 'customer_turn'
                }
                snippets.append(snippet)
                
                # 2. Dealer+Customer pair
                if prev_dealership_text:
                    pair_text = f"{prev_dealership_text} | {text}"
                    if not has_pii(pair_text):
                        snippet_pair = {
                            'conversation_id': conv_id,
                            'turn_index': turn.get('turn_idx', turn_idx),
                            'customer_text': text,
                            'prev_dealership_text': prev_dealership_text,
                            'scenario': scenario,
                            'stage': stage,
                            'persona': None,
                            'snippet_type': 'dealer_customer_pair',
                            'pair_text': pair_text  # Store combined text
                        }
                        snippets.append(snippet_pair)
                
                # 3. 3-turn window (sliding window)
                if len(prev_turns) >= 3:
                    # Create window from last 3 turns
                    window_turns = prev_turns[-3:]
                    window_texts = [t['text'] for t in window_turns]
                    window_text = " | ".join(window_texts)
                    
                    if not has_pii(window_text):
                        snippet_window = {
                            'conversation_id': conv_id,
                            'turn_index': turn.get('turn_idx', turn_idx),
                            'customer_text': text,
                            'prev_dealership_text': prev_dealership_text,
                            'scenario': scenario,
                            'stage': stage,
                            'persona': None,
                            'snippet_type': 'three_turn_window',
                            'window_text': window_text  # Store window text
                        }
                        snippets.append(snippet_window)
                
                # 4. Sentence chunks (split customer message)
                sentences = split_sentences(text)
                if len(sentences) > 1:
                    # Create snippet for each sentence
                    for sent_idx, sentence in enumerate(sentences):
                        sentence = sentence.strip()
                        if sentence and len(sentence) > 5:  # Minimum length
                            if not has_pii(sentence):
                                snippet_chunk = {
                                    'conversation_id': conv_id,
                                    'turn_index': turn.get('turn_idx', turn_idx),
                                    'customer_text': sentence,  # Just the sentence
                                    'prev_dealership_text': prev_dealership_text,
                                    'scenario': scenario,
                                    'stage': stage,
                                    'persona': None,
                                    'snippet_type': 'sentence_chunk',
                                    'sentence_index': sent_idx,
                                    'original_customer_text': text  # Keep reference to full text
                                }
                                snippets.append(snippet_chunk)
    
    return snippets


def main():
    """Main function to expand snippets."""
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "out" / "dataset_post_sales_turns.json"
    labels_file = base_dir / "out" / "labels.jsonl"
    output_file = base_dir / "out" / "snippets_expanded.jsonl"
    
    # Load dataset
    print(f"Loading dataset from {input_file}...")
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        print("Run previous scripts to generate dataset_post_sales_turns.json first!")
        return
    
    with open(input_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    conversations = dataset.get('conversations', [])
    print(f"Loaded {len(conversations)} conversations")
    
    # Load labels
    print(f"Loading labels from {labels_file}...")
    labels_dict = load_labels(labels_file)
    print(f"Loaded labels for {len(labels_dict)} conversations")
    
    # Expand snippets
    print("Expanding snippets (creating multiple retrieval units per conversation)...")
    snippets = expand_snippets(conversations, labels_dict)
    print(f"Generated {len(snippets)} expanded snippets")
    
    # Statistics by snippet type
    snippet_types = {}
    for snippet in snippets:
        stype = snippet.get('snippet_type', 'unknown')
        snippet_types[stype] = snippet_types.get(stype, 0) + 1
    
    print(f"\nSnippet type distribution:")
    for stype, count in sorted(snippet_types.items()):
        print(f"  {stype}: {count}")
    
    # Write JSONL file
    print(f"\nWriting expanded snippets to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for snippet in snippets:
            f.write(json.dumps(snippet, ensure_ascii=False) + '\n')
    
    # Additional statistics
    scenarios = {}
    stages = {}
    for snippet in snippets:
        scenario = snippet.get('scenario', 'unknown')
        stage = snippet.get('stage', 'unknown')
        scenarios[scenario] = scenarios.get(scenario, 0) + 1
        stages[stage] = stages.get(stage, 0) + 1
    
    print(f"\n✅ Snippet expansion complete!")
    print(f"\nSummary:")
    print(f"  Total expanded snippets: {len(snippets)}")
    print(f"  Expansion factor: ~{len(snippets) / max(len(conversations), 1):.1f}x")
    print(f"  Scenario distribution:")
    for scenario, count in sorted(scenarios.items(), key=lambda x: -x[1])[:10]:
        print(f"    {scenario}: {count}")
    
    print(f"\nOutput file: {output_file}")
    print(f"\nNext step: Run scripts/16_build_index.py with snippets_expanded.jsonl")


if __name__ == "__main__":
    main()
