# WhatsApp Chat Text Extractor

This system automatically unzips all WhatsApp chat ZIP files and extracts only the text files, organizing them in a clean structure.

## Features

- ✅ Extracts text files from all ZIP files in one go
- ✅ Places all text files in a single folder with unique names
- ✅ Backs up original ZIP files after processing
- ✅ Detailed logging and progress tracking
- ✅ Handles various text file formats
- ✅ Error handling and recovery
- ✅ Statistics and summary reporting

## Quick Start

### Option 1: Simple Shell Script (Recommended)
```bash
chmod +x run_extraction.sh
./run_extraction.sh
```

### Option 2: Direct Python Execution
```bash
python3 unzip_extractor.py
```

## What It Does

1. **Scans** the current directory for all `.zip` files
2. **Extracts** only text files from each ZIP (`.txt`, `.log`, `.csv`, etc.)
3. **Places** all text files in `extracted_texts/` folder with unique names
4. **Backs up** original ZIP files to `backup_zips/` folder
5. **Logs** all activities to `unzip_extraction.log`

## Output Structure

```
extracted_texts/
├── Chat de WhatsApp con +52 55 2092 9060_from_00000294-Chat de WhatsApp con +52 55 2092 9060.txt
├── Chat de WhatsApp con +52 55 4089 7467_from_00000295-Chat de WhatsApp con +52 55 4089 7467.txt
├── Chat de WhatsApp con +52 55 3357 3053_from_00000296-Chat de WhatsApp con +52 55 3357 3053.txt
└── ... (all text files in one folder)
```

## Advanced Usage

### Custom Directories
```bash
python3 unzip_extractor.py --source /path/to/zips --output /path/to/output
```

### No Backup (Keep Original ZIPs)
```bash
python3 unzip_extractor.py --no-backup
```

### Cleanup Empty Directories
```bash
python3 unzip_extractor.py --cleanup
```

### All Options
```bash
python3 unzip_extractor.py --source . --output extracted_texts --backup backup_zips --cleanup
```

## Command Line Options

- `--source`: Source directory containing ZIP files (default: current directory)
- `--output`: Output directory for extracted text files (default: `extracted_texts`)
- `--backup`: Backup directory for processed ZIP files (default: `backup_zips`)
- `--no-backup`: Don't backup ZIP files after extraction
- `--cleanup`: Remove empty directories after extraction

## Supported Text File Types

The system recognizes and extracts:
- `.txt` files
- `.log` files
- `.csv` files
- `.json` files
- `.xml` files
- `.html` and `.htm` files
- Files with patterns like `_chat.txt`, `chat.txt`, `messages.txt`, etc.

## Requirements

- Python 3.6 or higher
- No additional packages required (uses only standard library)

## Troubleshooting

### Check Logs
If something goes wrong, check the `unzip_extraction.log` file for detailed error information.

### Bad ZIP Files
The system will skip corrupted ZIP files and continue processing the rest.

### Permission Issues
Make sure you have read/write permissions in the current directory.

## Example Output

```
==================================================
EXTRACTION SUMMARY
==================================================
Total ZIP files processed: 84
Successful extractions: 82
Failed extractions: 2
Total text files extracted: 82
Total size extracted: 1,234,567 bytes
Output directory: /path/to/extracted_texts
Backup directory: /path/to/backup_zips
==================================================
```

## Safety Features

- Original ZIP files are backed up before deletion
- Detailed logging of all operations
- Error handling prevents crashes
- Progress tracking and statistics
- Non-destructive operation (keeps originals unless specified) 