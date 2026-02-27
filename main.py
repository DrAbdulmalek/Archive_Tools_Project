#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Archive Tools Project
This script provides a unified interface to process various file types and extract text content
for AI model training purposes.
"""

import sys
import os
from pathlib import Path

def main():
    """Main function to demonstrate the integrated project"""
    print("=" * 80)
    print("🗂️  Archive Tools Project - Main Interface")
    print("   Comprehensive text extraction and classification tool for AI model training")
    print("=" * 80)
    
    # Import the main processing script
    try:
        from scripts.zip_rar_folder2txt import process_single_item
        print("\n✅ Successfully imported processing modules")
        
        # Display supported features
        print("\n📋 Supported Features:")
        print("   • Archive extraction (ZIP, RAR, TAR, GZ, etc.)")
        print("   • Document processing (PDF, DOCX, XLSX)")
        print("   • Text extraction from various formats")
        print("   • Advanced PDF processing with OCR support")
        print("   • Database content extraction (SQLite, etc.)")
        print("   • HTML content extraction and cleaning")
        print("   • Large file splitting and organization")
        print("   • Content classification and organization")
        print("   • Preparation of training data for AI models")
        
        print(f"\n📁 Current workspace: {os.getcwd()}")
        print("📦 Available data samples:")
        
        # Show available data files
        data_dir = Path("data")
        if data_dir.exists():
            for file in data_dir.glob("*"):
                print(f"   • {file.name}")
        else:
            print("   • No data directory found")
            
        print(f"\n🔧 Available scripts in scripts/:")
        scripts_dir = Path("scripts")
        if scripts_dir.exists():
            for script in scripts_dir.glob("*.py"):
                print(f"   • {script.name}")
        else:
            print("   • No scripts directory found")
        
        print("\n" + "=" * 80)
        print("🚀 To use the tool, run one of these commands:")
        print("   python -m scripts.zip_rar_folder2txt [options] <input_file_or_directory>")
        print("   python -m scripts.extract_pdf_advanced <pdf_file>")
        print("   python -m scripts.split_big_text_enhanced <large_text_file>")
        print("   python -m scripts.unified_archive_extractor <archive_file>")
        print("=" * 80)
        
        # Provide usage examples
        print("\n💡 Usage Examples:")
        print("   # Extract all text from an archive:")
        print("   python -m scripts.zip_rar_folder2txt /path/to/archive.zip")
        print()
        print("   # Process PDF with OCR:")
        print("   python -m scripts.zip_rar_folder2txt --ocr /path/to/document.pdf")
        print()
        print("   # Process database via Excel:")
        print("   python -m scripts.zip_rar_folder2txt --via-excel /path/to/database.db")
        print()
        print("   # Process entire folder:")
        print("   python -m scripts.zip_rar_folder2txt /path/to/folder/")
        print()
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importing processing modules: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
    else:
        print("\n✅ Project successfully loaded and ready for use!")
        print("   Use the individual scripts in the scripts/ directory for specific tasks.")