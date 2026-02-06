#!/usr/bin/env python3
"""
Step 1.1: Data Inventory
Analyze all files in extracted_texts/ and create raw_manifest.csv
"""

import os
import re
import csv
from pathlib import Path
from typing import Dict, List

# WhatsApp message pattern: DD/M/YYYY, HH:MM a. m./p. m. - Sender: Text
WHATSAPP_PATTERN = re.compile(r'\d{1,2}/\d{1,2}/\d{4}, \d{1,2}:\d{2} [ap]\. m\.')
CONVERSATION_DELIMITER = "start conversation"


def analyze_file(filepath: Path) -> Dict[str, any]:
    """Analyze a single file and return metadata."""
    filename = filepath.name
    
    try:
        # Try UTF-8 first, fallback to latin-1 if needed
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                encoding = 'utf-8'
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
                encoding = 'latin-1'
        
        lines = content.split('\n')
        line_count = len(lines)
        
        # Check for WhatsApp format
        has_timestamps = bool(WHATSAPP_PATTERN.search(content))
        
        # Check for sender pattern (look for " - Sender: " pattern)
        has_sender = bool(re.search(r' - .+?:', content))
        
        # Count conversation delimiters
        estimated_conversations = content.count(CONVERSATION_DELIMITER)
        if estimated_conversations == 0 and has_timestamps:
            # Single conversation file
            estimated_conversations = 1
        
        # Determine format
        format_type = "whatsapp" if has_timestamps and has_sender else "unknown"
        
        # Check for anomalies
        notes = []
        if line_count == 0:
            notes.append("empty_file")
        if not has_timestamps:
            notes.append("no_timestamps")
        if not has_sender:
            notes.append("no_sender")
        if encoding != 'utf-8':
            notes.append(f"encoding_{encoding}")
        
        return {
            "raw_file": filename,
            "format": format_type,
            "has_timestamps": has_timestamps,
            "has_sender": has_sender,
            "delimiter": CONVERSATION_DELIMITER if estimated_conversations > 1 else "none",
            "line_count": line_count,
            "estimated_conversations": estimated_conversations,
            "encoding": encoding,
            "notes": "; ".join(notes) if notes else "ok"
        }
    
    except Exception as e:
        return {
            "raw_file": filename,
            "format": "error",
            "has_timestamps": False,
            "has_sender": False,
            "delimiter": "unknown",
            "line_count": 0,
            "estimated_conversations": 0,
            "encoding": "unknown",
            "notes": f"error: {str(e)}"
        }


def main():
    """Main function to generate inventory."""
    # Paths
    base_dir = Path(__file__).parent.parent
    extracted_dir = base_dir / "extracted_texts"
    output_file = base_dir / "out" / "raw_manifest.csv"
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Find all .txt files
    txt_files = sorted(extracted_dir.glob("*.txt"))
    
    if not txt_files:
        print(f"Warning: No .txt files found in {extracted_dir}")
        return
    
    print(f"Analyzing {len(txt_files)} files...")
    
    # Analyze each file
    results = []
    for txt_file in txt_files:
        result = analyze_file(txt_file)
        results.append(result)
        print(f"  {result['raw_file']}: {result['estimated_conversations']} conversations, {result['line_count']} lines")
    
    # Write CSV
    fieldnames = [
        "raw_file", "format", "has_timestamps", "has_sender", 
        "delimiter", "line_count", "estimated_conversations", 
        "encoding", "notes"
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    # Print summary
    total_conversations = sum(r['estimated_conversations'] for r in results)
    total_lines = sum(r['line_count'] for r in results)
    whatsapp_files = sum(1 for r in results if r['format'] == 'whatsapp')
    
    print(f"\nSummary:")
    print(f"  Total files: {len(txt_files)}")
    print(f"  WhatsApp format: {whatsapp_files}")
    print(f"  Total conversations: {total_conversations}")
    print(f"  Total lines: {total_lines}")
    print(f"\nManifest saved to: {output_file}")


if __name__ == "__main__":
    main()
