#!/bin/bash

# WhatsApp Chat Extraction Script
# This script runs the Python unzipper to extract text files from all ZIP files

echo "WhatsApp Chat Text Extractor"
echo "============================"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Make the Python script executable
chmod +x unzip_extractor.py

# Run the extraction
echo "Starting extraction process..."
echo "This will:"
echo "- Extract text files from all ZIP files in the current directory"
echo "- Organize them in 'extracted_texts' folder"
echo "- Backup original ZIP files to 'backup_zips' folder"
echo "- Create a detailed log file"
echo ""

# Run with default settings
python3 unzip_extractor.py

echo ""
echo "Extraction completed! Check the 'extracted_texts' folder for your text files."
echo "Original ZIP files have been backed up to 'backup_zips' folder."
echo "Check 'unzip_extraction.log' for detailed information." 