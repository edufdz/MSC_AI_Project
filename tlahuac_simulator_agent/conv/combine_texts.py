#!/usr/bin/env python3
"""
Text File Combiner
Combines all extracted WhatsApp chat text files into one file with a specific format.
"""

import os
from pathlib import Path
import argparse

def combine_text_files(input_dir="extracted_texts", output_file="combined_chats.txt"):
    """Combine all text files into one file with the specified format."""
    
    input_path = Path(input_dir)
    output_path = Path(output_file)
    
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return False
    
    # Get all text files
    text_files = list(input_path.glob("*.txt"))
    
    if not text_files:
        print(f"No text files found in '{input_dir}'.")
        return False
    
    print(f"Found {len(text_files)} text files to combine...")
    
    # Sort files for consistent ordering
    text_files.sort()
    
    with open(output_path, 'w', encoding='utf-8') as output:
        for i, text_file in enumerate(text_files, 1):
            print(f"Processing {i}/{len(text_files)}: {text_file.name}")
            
            # Write the conversation header
            output.write("start conversation\n")
            output.write("-" * 22 + "\n")
            
            # Read and write the actual text content
            try:
                with open(text_file, 'r', encoding='utf-8') as input_file:
                    content = input_file.read().strip()
                    output.write(content)
            except Exception as e:
                print(f"Error reading {text_file}: {e}")
                output.write(f"[Error reading file: {e}]\n")
            
            # Write the separator
            output.write("\n" + "-" * 11 + "\n\n")
    
    print(f"\n✅ Successfully combined {len(text_files)} files into '{output_file}'")
    print(f"📁 Output file size: {output_path.stat().st_size:,} bytes")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Combine all extracted text files into one file")
    parser.add_argument("--input", default="extracted_texts", help="Input directory containing text files (default: extracted_texts)")
    parser.add_argument("--output", default="combined_chats.txt", help="Output file name (default: combined_chats.txt)")
    
    args = parser.parse_args()
    
    success = combine_text_files(args.input, args.output)
    
    if success:
        print("\n🎉 Text combination completed successfully!")
    else:
        print("\n❌ Text combination failed.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 