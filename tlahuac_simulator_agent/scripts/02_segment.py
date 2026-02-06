#!/usr/bin/env python3
"""
Step 1.2: Conversation Segmentation
Split files into individual conversation blocks
"""

import os
import json
from pathlib import Path
from typing import List

CONVERSATION_DELIMITER = "start conversation"
DELIMITER_SEPARATOR = "----------------------"


def segment_file(filepath: Path) -> List[str]:
    """
    Split a file into conversation blocks.
    Returns list of conversation text blocks.
    """
    try:
        # Try UTF-8 first, fallback to latin-1
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []
    
    # Check if file has delimiter (multiple conversations)
    if CONVERSATION_DELIMITER in content:
        # Split on delimiter pattern
        # Pattern: "start conversation\n----------------------" or similar
        parts = content.split(CONVERSATION_DELIMITER)
        conversations = []
        
        for part in parts[1:]:  # Skip part before first delimiter
            # Remove separator line if present
            if part.startswith('\n' + DELIMITER_SEPARATOR):
                part = part[len('\n' + DELIMITER_SEPARATOR):].lstrip('\n')
            elif part.startswith(DELIMITER_SEPARATOR):
                part = part[len(DELIMITER_SEPARATOR):].lstrip('\n')
            
            # Clean up and add if not empty
            part = part.strip()
            if part:
                conversations.append(part)
        
        return conversations if conversations else [content.strip()]
    else:
        # Single conversation file
        content = content.strip()
        return [content] if content else []


def main():
    """Main function to segment all files."""
    base_dir = Path(__file__).parent.parent
    extracted_dir = base_dir / "extracted_texts"
    output_dir = base_dir / "out" / "parsed"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all .txt files
    txt_files = sorted(extracted_dir.glob("*.txt"))
    
    if not txt_files:
        print(f"Warning: No .txt files found in {extracted_dir}")
        return
    
    print(f"Segmenting {len(txt_files)} files...")
    
    total_conversations = 0
    file_conversation_map = {}
    
    for txt_file in txt_files:
        conversations = segment_file(txt_file)
        file_conversation_map[txt_file.name] = len(conversations)
        total_conversations += len(conversations)
        
        # Save each conversation block as JSON for next step
        for idx, conv_block in enumerate(conversations):
            # Create a safe filename
            base_name = txt_file.stem
            if len(conversations) == 1:
                output_filename = f"{base_name}.json"
            else:
                output_filename = f"{base_name}_conv{idx+1}.json"
            
            output_path = output_dir / output_filename
            
            # Store as JSON with metadata
            data = {
                "source_file": txt_file.name,
                "conversation_index": idx if len(conversations) > 1 else 0,
                "total_conversations_in_file": len(conversations),
                "raw_text": conv_block
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Total files processed: {len(txt_files)}")
    print(f"  Total conversations: {total_conversations}")
    
    # Show files with multiple conversations
    multi_conv_files = {k: v for k, v in file_conversation_map.items() if v > 1}
    if multi_conv_files:
        print(f"  Files with multiple conversations: {len(multi_conv_files)}")
        for filename, count in list(multi_conv_files.items())[:5]:
            print(f"    {filename}: {count} conversations")
    
    print(f"\nSegmented conversations saved to: {output_dir}")


if __name__ == "__main__":
    main()
