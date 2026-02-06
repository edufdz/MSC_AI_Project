#!/usr/bin/env python3
"""
WhatsApp Chat Unzipper and Text Extractor
This script unzips all zip files in the current directory and extracts only text files.
"""

import os
import zipfile
import shutil
import logging
from pathlib import Path
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unzip_extraction.log'),
        logging.StreamHandler()
    ]
)

class WhatsAppUnzipper:
    def __init__(self, source_dir=".", output_dir="extracted_texts", backup_dir="backup_zips"):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.backup_dir = Path(backup_dir)
        self.text_extensions = {'.txt', '.log', '.csv', '.json', '.xml', '.html', '.htm'}
        
        # Create directories
        self.output_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_zips': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_text_files': 0,
            'total_size_extracted': 0
        }
    
    def is_text_file(self, filename):
        """Check if a file is a text file based on extension or content."""
        file_path = Path(filename)
        
        # Check by extension
        if file_path.suffix.lower() in self.text_extensions:
            return True
        
        # Check by filename patterns (common WhatsApp export patterns)
        text_patterns = [
            '_chat.txt',
            'chat.txt',
            'messages.txt',
            'export.txt',
            'conversation.txt'
        ]
        
        for pattern in text_patterns:
            if pattern in filename.lower():
                return True
        
        return False
    
    def extract_zip_file(self, zip_path):
        """Extract text files from a single zip file."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                extracted_count = 0
                
                for file_info in zip_ref.filelist:
                    filename = file_info.filename
                    
                    # Skip directories
                    if filename.endswith('/'):
                        continue
                    
                    # Check if it's a text file
                    if self.is_text_file(filename):
                        try:
                            # Create a unique filename to avoid conflicts
                            base_name = Path(filename).stem
                            extension = Path(filename).suffix
                            zip_name = zip_path.stem
                            
                            # Create unique filename: original_name_from_zip.txt
                            unique_filename = f"{base_name}_from_{zip_name}{extension}"
                            
                            # Extract the file directly to output directory
                            zip_ref.extract(file_info, self.output_dir)
                            original_path = self.output_dir / filename
                            
                            # Rename to unique filename
                            new_path = self.output_dir / unique_filename
                            if original_path.exists():
                                original_path.rename(new_path)
                            
                            # Get file size
                            file_size = new_path.stat().st_size
                            self.stats['total_size_extracted'] += file_size
                            
                            logging.info(f"Extracted: {unique_filename} from {zip_path.name} ({file_size} bytes)")
                            extracted_count += 1
                            
                        except Exception as e:
                            logging.error(f"Failed to extract {filename} from {zip_path.name}: {e}")
                            continue
                
                if extracted_count > 0:
                    self.stats['successful_extractions'] += 1
                    self.stats['total_text_files'] += extracted_count
                    logging.info(f"Successfully extracted {extracted_count} text files from {zip_path.name}")
                else:
                    logging.warning(f"No text files found in {zip_path.name}")
                
                return extracted_count > 0
                
        except zipfile.BadZipFile:
            logging.error(f"Bad zip file: {zip_path}")
            self.stats['failed_extractions'] += 1
            return False
        except Exception as e:
            logging.error(f"Error processing {zip_path}: {e}")
            self.stats['failed_extractions'] += 1
            return False
    
    def backup_zip_file(self, zip_path):
        """Move zip file to backup directory after successful extraction."""
        try:
            backup_path = self.backup_dir / zip_path.name
            shutil.move(str(zip_path), str(backup_path))
            logging.info(f"Backed up: {zip_path.name}")
        except Exception as e:
            logging.error(f"Failed to backup {zip_path.name}: {e}")
    
    def process_all_zips(self, backup_after_extraction=True):
        """Process all zip files in the source directory."""
        zip_files = list(self.source_dir.glob("*.zip"))
        self.stats['total_zips'] = len(zip_files)
        
        if not zip_files:
            logging.warning("No zip files found in the source directory")
            return
        
        logging.info(f"Found {len(zip_files)} zip files to process")
        
        for zip_file in zip_files:
            logging.info(f"Processing: {zip_file.name}")
            
            if self.extract_zip_file(zip_file):
                if backup_after_extraction:
                    self.backup_zip_file(zip_file)
            else:
                logging.error(f"Failed to extract from {zip_file.name}")
        
        self.print_summary()
    
    def print_summary(self):
        """Print extraction summary."""
        print("\n" + "="*50)
        print("EXTRACTION SUMMARY")
        print("="*50)
        print(f"Total ZIP files processed: {self.stats['total_zips']}")
        print(f"Successful extractions: {self.stats['successful_extractions']}")
        print(f"Failed extractions: {self.stats['failed_extractions']}")
        print(f"Total text files extracted: {self.stats['total_text_files']}")
        print(f"Total size extracted: {self.stats['total_size_extracted']:,} bytes")
        print(f"Output directory: {self.output_dir.absolute()}")
        if self.stats['successful_extractions'] > 0:
            print(f"Backup directory: {self.backup_dir.absolute()}")
        print("="*50)
    
    def cleanup_empty_dirs(self):
        """Remove empty directories from output."""
        for root, dirs, files in os.walk(self.output_dir, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        logging.info(f"Removed empty directory: {dir_path}")
                except Exception as e:
                    logging.error(f"Failed to remove directory {dir_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Extract text files from WhatsApp chat ZIP files")
    parser.add_argument("--source", default=".", help="Source directory containing ZIP files (default: current directory)")
    parser.add_argument("--output", default="extracted_texts", help="Output directory for extracted text files")
    parser.add_argument("--backup", default="backup_zips", help="Backup directory for processed ZIP files")
    parser.add_argument("--no-backup", action="store_true", help="Don't backup ZIP files after extraction")
    parser.add_argument("--cleanup", action="store_true", help="Remove empty directories after extraction")
    
    args = parser.parse_args()
    
    # Create unzipper instance
    unzipper = WhatsAppUnzipper(
        source_dir=args.source,
        output_dir=args.output,
        backup_dir=args.backup
    )
    
    # Process all zip files
    unzipper.process_all_zips(backup_after_extraction=not args.no_backup)
    
    # Cleanup if requested
    if args.cleanup:
        unzipper.cleanup_empty_dirs()
    
    logging.info("Extraction process completed!")

if __name__ == "__main__":
    main() 