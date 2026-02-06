#!/usr/bin/env python3
"""
Step 1.3: Parse Messages
Extract timestamp, sender, and text from WhatsApp message format
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# WhatsApp timestamp pattern: DD/M/YYYY, HH:MM a. m./p. m.
# Note: WhatsApp uses non-breaking spaces (\u202f), so we match both regular and non-breaking spaces
TIMESTAMP_PATTERN = re.compile(
    r'(\d{1,2}/\d{1,2}/\d{4}, \d{1,2}:\d{2}\s+[ap]\.\s*m\.)'
)


def parse_timestamp(ts_str: str) -> Optional[str]:
    """
    Parse WhatsApp timestamp to ISO8601 format.
    Input: "16/7/2025, 10:02 a. m." (may have non-breaking spaces)
    Output: "2025-07-16T10:02:00-06:00" or None if parsing fails
    """
    try:
        # Parse format: DD/M/YYYY, HH:MM a. m./p. m.
        # Normalize spaces (replace non-breaking spaces with regular spaces)
        ts_str = ts_str.replace('\u202f', ' ').replace('\u00a0', ' ').strip()
        
        # Split date and time
        date_part, time_part = ts_str.split(',')
        day, month, year = map(int, date_part.strip().split('/'))
        
        # Parse time - handle multiple spaces
        time_part = ' '.join(time_part.split())  # Normalize whitespace
        # Split on last space to separate hour:minute from am/pm
        parts = time_part.rsplit(' ', 1)
        if len(parts) != 2:
            return None
        
        hour_min_str, am_pm = parts
        hour, minute = map(int, hour_min_str.split(':'))
        
        # Convert to 24-hour format
        am_pm = am_pm.lower().strip()
        if 'p' in am_pm:
            if hour != 12:
                hour += 12
        elif 'a' in am_pm:
            if hour == 12:
                hour = 0
        
        # Create datetime (assuming Mexico City timezone UTC-6)
        dt = datetime(year, month, day, hour, minute)
        
        # Return ISO8601 format (we'll assume UTC-6 for Mexico City)
        # Note: This is approximate - actual timezone handling would require tzinfo
        return dt.strftime("%Y-%m-%dT%H:%M:00-06:00")
    
    except Exception as e:
        return None


def parse_messages(conversation_text: str) -> List[Dict]:
    """
    Parse conversation text into list of message objects.
    Handles multi-line messages by accumulating until next timestamp.
    """
    messages = []
    lines = conversation_text.split('\n')
    
    current_message = None
    current_text_lines = []
    
    for line in lines:
        # Check if line starts with a timestamp
        ts_match = TIMESTAMP_PATTERN.match(line)
        
        if ts_match:
            # Save previous message if exists
            if current_message is not None:
                current_message['text_raw'] = '\n'.join(current_text_lines).strip()
                if current_message['text_raw']:  # Only add if not empty
                    messages.append(current_message)
            
            # Parse the new line
            ts_raw = ts_match.group(1)
            rest = line[len(ts_raw):].strip()
            
            # Check if it has sender pattern: " - Sender: text"
            if rest.startswith('- '):
                rest = rest[2:]  # Remove " - "
                
                # Try to find sender (everything before ":")
                if ': ' in rest:
                    parts = rest.split(': ', 1)
                    speaker = parts[0].strip()
                    text_start = parts[1].strip()
                else:
                    # No colon, might be system message
                    speaker = 'system'
                    text_start = rest
            else:
                # No " - " pattern, treat as system message
                speaker = 'system'
                text_start = rest
            
            current_message = {
                'ts_raw': ts_raw,
                'ts': parse_timestamp(ts_raw),
                'speaker_raw': speaker,
                'text_raw': '',  # Will be filled with accumulated text
            }
            current_text_lines = [text_start] if text_start else []
        
        elif current_message is not None:
            # Continuation of current message (multi-line)
            # Preserve the line as-is (including empty lines for formatting)
            current_text_lines.append(line)
    
    # Don't forget the last message
    if current_message is not None:
        current_message['text_raw'] = '\n'.join(current_text_lines).strip()
        # Include message even if empty (system messages might be empty)
        # But skip if speaker is 'system' and text is truly empty
        if current_message['text_raw'] or current_message.get('speaker_raw') != 'system':
            messages.append(current_message)
    
    # Add index to each message
    for idx, msg in enumerate(messages):
        msg['idx'] = idx
    
    return messages


def main():
    """Main function to parse all segmented conversations."""
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "out" / "parsed"
    output_dir = base_dir / "out" / "parsed"
    
    # Find all JSON files from segmentation step
    json_files = sorted(input_dir.glob("*.json"))
    
    if not json_files:
        print(f"Warning: No JSON files found in {input_dir}")
        print("Run 02_segment.py first!")
        return
    
    print(f"Parsing {len(json_files)} conversations...")
    
    parsed_count = 0
    total_messages = 0
    
    for json_file in json_files:
        try:
            # Load segmented conversation
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            raw_text = data.get('raw_text', '')
            if not raw_text:
                continue
            
            # Parse messages
            messages = parse_messages(raw_text)
            
            if not messages:
                # Debug: check if raw_text has content
                if raw_text.strip():
                    print(f"  Warning: No messages found in {json_file.name} (has {len(raw_text)} chars)")
                    # Show first few lines for debugging
                    first_lines = '\n'.join(raw_text.split('\n')[:3])
                    print(f"    First lines: {first_lines[:100]}...")
                continue
            
            # Update data with parsed messages
            data['messages'] = messages
            data['message_count'] = len(messages)
            
            # Save updated JSON
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            parsed_count += 1
            total_messages += len(messages)
            
            if parsed_count % 20 == 0:
                print(f"  Processed {parsed_count} conversations, {total_messages} messages...")
        
        except Exception as e:
            print(f"  Error processing {json_file.name}: {e}")
            continue
    
    print(f"\nSummary:")
    print(f"  Conversations parsed: {parsed_count}")
    print(f"  Total messages: {total_messages}")
    print(f"  Average messages per conversation: {total_messages / parsed_count if parsed_count > 0 else 0:.1f}")


if __name__ == "__main__":
    main()
