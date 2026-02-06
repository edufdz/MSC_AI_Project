#!/usr/bin/env python3
"""
Step 1.4: Normalize Text
Light normalization while preserving customer voice
"""

import re
import json
import unicodedata
from pathlib import Path
from typing import Dict


def normalize_text(text: str) -> str:
    """
    Normalize text with light processing:
    - Trim whitespace
    - Normalize line breaks
    - Preserve punctuation, emojis, capitalization
    - Keep WhatsApp formatting markers
    """
    if not text:
        return ""
    
    # Unicode normalization (NFC)
    text = unicodedata.normalize('NFC', text)
    
    # Normalize line breaks: \r\n or \r -> \n
    text = re.sub(r'\r\n|\r', '\n', text)
    
    # Collapse multiple newlines (3+ -> 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Trim leading/trailing whitespace per line, but preserve internal spacing
    lines = text.split('\n')
    normalized_lines = [line.rstrip() for line in lines]
    
    # Remove leading empty lines
    while normalized_lines and not normalized_lines[0].strip():
        normalized_lines.pop(0)
    
    # Remove trailing empty lines
    while normalized_lines and not normalized_lines[-1].strip():
        normalized_lines.pop()
    
    text = '\n'.join(normalized_lines)
    
    # Final trim of leading/trailing whitespace
    text = text.strip()
    
    return text


def main():
    """Main function to normalize all parsed conversations."""
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "out" / "parsed"
    
    # Find all JSON files
    json_files = sorted(input_dir.glob("*.json"))
    
    if not json_files:
        print(f"Warning: No JSON files found in {input_dir}")
        print("Run 03_parse.py first!")
        return
    
    print(f"Normalizing {len(json_files)} conversations...")
    
    processed_count = 0
    
    for json_file in json_files:
        try:
            # Load parsed conversation
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            messages = data.get('messages', [])
            if not messages:
                continue
            
            # Normalize text for each message
            for msg in messages:
                text_raw = msg.get('text_raw', '')
                msg['text'] = normalize_text(text_raw)
            
            # Save updated JSON
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            processed_count += 1
            
            if processed_count % 20 == 0:
                print(f"  Processed {processed_count} conversations...")
        
        except Exception as e:
            print(f"  Error processing {json_file.name}: {e}")
            continue
    
    print(f"\nSummary:")
    print(f"  Conversations normalized: {processed_count}")


if __name__ == "__main__":
    main()
