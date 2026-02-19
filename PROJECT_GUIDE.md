# 🗂️ Archive Tools Project - Complete Guide

## Overview

This project is a comprehensive suite of tools designed to extract, classify, and organize text content from various file formats for use as training data for AI models. The tools support archives (ZIP, RAR, TAR), documents (PDF, DOCX, XLSX), databases, and many other formats.

## 📁 Project Structure

```
archive_tools_project/
├── 📄 README.md                    # Project overview
├── 📄 PROJECT_GUIDE.md            # This guide
├── 📄 LICENSE                     # MIT License
├── 📄 requirements.txt            # Required libraries
├── 📄 main.py                     # Entry point
│
├── 📂 scripts/                     # Core processing scripts
│   ├── extract_archive_to_text.py     # Basic archive extraction
│   ├── extract_pdf_advanced.py        # Advanced PDF processing with OCR
│   ├── split_big_text_enhanced.py     # Large file splitting
│   ├── unified_archive_extractor.py   # Unified extraction interface
│   ├── zip_rar_folder2txt.py          # Main processing script
│   ├── zip_rar_folder2txt_split.py    # Split version
│   └── py_txt_zip_rar_folder2txt.py   # Extended version
│
├── 📂 data/                        # Sample data and outputs
│   ├── html_text.txt                  # Sample HTML extracted text
│   └── Text_snippets-main_zip_contents.txt  # Sample archive content
│
└── 📂 docs/                        # Documentation
    └── chat-معالجة وتصنيف المحتوى.txt  # Arabic processing notes
```

## 🚀 Key Features

### 1. Archive Extraction
- **ZIP, RAR, TAR, GZ Support**: Full extraction of compressed archives
- **Multi-part Archives**: Recognition and handling of split archives
- **Nested Archive Support**: Recursive extraction of nested archives

### 2. Document Processing
- **PDF Processing**: Advanced extraction with OCR support
- **Word Documents**: Text and table extraction from DOCX
- **Excel Files**: Conversion of spreadsheets to text format
- **HTML Content**: Cleaning and extraction of text from HTML

### 3. Database Content Extraction
- **SQLite Support**: Direct extraction of database tables
- **Excel Export**: Option to export via Excel format
- **Structured Output**: Tab-separated values for easy parsing

### 4. Text Classification & Organization
- **Paragraph-by-paragraph processing**: Detailed content analysis
- **Line-by-line extraction**: Preserves document structure
- **Word-level tokenization**: For fine-grained analysis
- **Content categorization**: Organized output by content type

### 5. AI Model Preparation
- **Clean Text Output**: Ready for model training
- **Consistent Formatting**: Standardized output format
- **Metadata Preservation**: File information maintained
- **Large File Handling**: Splits oversized files appropriately

## 📦 Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. For enhanced functionality, install additional tools:
```bash
# For RAR support (alternative method)
sudo apt-get install unrar-free  # On Debian/Ubuntu
# OR
brew install unrar  # On macOS

# For OCR support
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-ara  # On Debian/Ubuntu
# OR
brew install tesseract tesseract-lang  # On macOS
```

## 🔧 Usage Examples

### Basic Usage
Process a single file or folder:
```bash
python -m scripts.zip_rar_folder2txt /path/to/file_or_folder
```

### With Options
```bash
# Process PDF with OCR enabled
python -m scripts.zip_rar_folder2txt --ocr document.pdf

# Process database via Excel (recommended for complex databases)
python -m scripts.zip_rar_folder2txt --via-excel database.db

# Process multiple files
python -m scripts.zip_rar_folder2txt file1.zip file2.pdf folder/
```

### Advanced PDF Processing
```bash
python -m scripts.extract_pdf_advanced document.pdf
```

### Large File Splitting
```bash
python -m scripts.split_big_text_enhanced large_file.txt
```

## 📊 Supported File Types

### Text Files
`.txt`, `.py`, `.js`, `.html`, `.css`, `.json`, `.xml`, `.csv`, `.md`, `.yml`, `.yaml`, `.ini`, `.cfg`, `.conf`, `.java`, `.c`, `.cpp`, `.h`, `.cs`, `.php`, `.rb`, `.go`, `.rs`, `.swift`, `.kt`, `.sql`, `.sh`, `.bat`, `.ps1`, and more.

### Document Files
`.pdf`, `.docx`, `.xls`, `.xlsx`

### Database Files
`.db`, `.sqlite`, `.sqlite3`

### Archive Files
`.zip`, `.rar`, `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`, `.gz`

## 🤖 AI Model Training Preparation

The project is specifically designed to prepare content for AI model training:

1. **Content Extraction**: Extracts text content while preserving meaningful structure
2. **Format Normalization**: Converts various formats to consistent text representation
3. **Classification**: Organizes content by type and source
4. **Preprocessing**: Cleans and prepares text for model ingestion
5. **Output Organization**: Creates structured output suitable for training pipelines

## 📋 Processing Workflow

For each file or directory processed, the system:

1. **Identifies the file type** based on extension and content
2. **Applies appropriate extraction method** for the detected format
3. **Processes content paragraph by paragraph, line by line, and word by word**
4. **Classifies and organizes content** with metadata preservation
5. **Generates comprehensive, classified reference** in text format
6. **Creates organized output structure** suitable for AI model training

## ⚠️ Important Notes

1. **Hidden Folders Ignored**: Folders starting with `.` are ignored along with `__pycache__` and `venv`
2. **Binary Files Skipped**: Binary files are generally ignored unless they're specific formats like databases
3. **Model Folder Detection**: Files in `models/` folders are registered by name only (content not extracted) to avoid processing large model files
4. **Split Archives**: Multi-part archives (like `.z01`, `.r00`) are detected and ignored to prevent partial extraction

## 🛠️ Customization

The scripts can be customized for specific needs:

- Modify `TEXT_EXTENSIONS` in the main script to include additional text-based formats
- Adjust processing parameters in individual scripts
- Create custom extraction methods for specialized file formats

## 📞 Support

For questions or issues, please refer to the original repository or create an issue with specific details about your use case.

---

<p align="center">
  <b>Built with ❤️ for the Arabic community and AI research</b>
</p>