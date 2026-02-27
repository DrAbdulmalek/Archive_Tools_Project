#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ultimate Text Classifier - Fast Version
Lightweight version without semantic deduplication for faster processing
Supports Arabic and English text classification using local AI models
"""

import os
import sys
import json
import logging
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import re

# Third-party imports
try:
    import requests
except ImportError as e:
    print(f"Missing required packages. Please install: pip install requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('classification_fast.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateFastClassifier:
    """
    Lightweight text classifier without semantic deduplication for faster processing
    """
    
    def __init__(self, 
                 ollama_model: str = "qwen2.5",
                 output_dir: str = "~/classified_ultimate_fast"):
        
        self.ollama_model = ollama_model
        self.output_dir = Path(output_dir).expanduser()
        self.knowledge_file = Path("user_knowledge_fast.json")
        
        # Initialize components
        self.user_knowledge = {}
        
        # Load user knowledge if exists
        self.load_user_knowledge()
        
        # Create output directories
        self.create_directories()
        
    def create_directories(self):
        """Create necessary output directories"""
        dirs = [
            self.output_dir / "classified",
            self.output_dir / "logs", 
            self.output_dir / "reports",
            self.output_dir / "classified" / "medical",
            self.output_dir / "classified" / "technical",
            self.output_dir / "classified" / "translation",
            self.output_dir / "classified" / "reference",
            self.output_dir / "classified" / "misc"
        ]
        
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
            
    def load_user_knowledge(self):
        """Load user corrections and preferences"""
        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    self.user_knowledge = json.load(f)
                logger.info(f"Loaded {len(self.user_knowledge)} user knowledge entries")
            except Exception as e:
                logger.error(f"Error loading user knowledge: {e}")
                
    def save_user_knowledge(self):
        """Save user corrections and preferences"""
        try:
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_knowledge, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.user_knowledge)} user knowledge entries")
        except Exception as e:
            logger.error(f"Error saving user knowledge: {e}")
            
    def detect_language(self, text: str) -> str:
        """Detect if text is Arabic or English"""
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if arabic_chars > english_chars:
            return "arabic"
        else:
            return "english"
    
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters while preserving Arabic/Persian/English
        text = re.sub(r'[^\w\s\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\u200C-\u200D\u200E\u200F\u202A-\u202E]', ' ', text)
        return text.strip()
    
    def call_ollama_api(self, prompt: str) -> Dict:
        """Call local Ollama API for classification"""
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9
            }
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return {"response": "Unknown", "error": str(e)}
    
    def classify_text(self, text: str) -> Dict:
        """Classify text using LLM with user knowledge"""
        # Check if we have a known pattern for this text
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.user_knowledge:
            logger.info(f"Using cached classification for text hash: {text_hash[:8]}")
            return self.user_knowledge[text_hash]
        
        # Create classification prompt
        lang = self.detect_language(text)
        text_preview = text[:500]  # Take first 500 chars for prompt
        
        prompt = f"""
You are an expert text classifier. Classify the following text into one of these categories:
- medical (medical content, health, diseases, treatments, anatomy)
- technical (technology, programming, computers, engineering, software)
- translation (bilingual content, translation work, language learning)
- reference (manuals, guides, documentation, tutorials)
- misc (other content)

Text ({lang}):
{text_preview}

Respond with only the category name followed by confidence score (0-100) in the format:
category: confidence

Examples:
- medical: 95
- technical: 80
- translation: 70
- reference: 85
- misc: 50
"""
        
        result = self.call_ollama_api(prompt)
        
        # Parse the response
        response_text = result.get("response", "misc: 50")
        parts = response_text.strip().split(": ")
        
        if len(parts) >= 2:
            category = parts[0].strip().lower()
            try:
                confidence = int(parts[1].split()[0])
            except:
                confidence = 50
        else:
            category = "misc"
            confidence = 50
            
        # Validate category
        valid_categories = ["medical", "technical", "translation", "reference", "misc"]
        if category not in valid_categories:
            category = "misc"
            confidence = 30
            
        classification_result = {
            "category": category,
            "confidence": min(max(confidence, 0), 100),
            "language": lang,
            "timestamp": datetime.now().isoformat(),
            "model_used": self.ollama_model
        }
        
        # Store in user knowledge for future use
        self.user_knowledge[text_hash] = classification_result
        
        return classification_result
    
    def process_file(self, file_path: Path) -> Optional[Dict]:
        """Process a single file and return classification result"""
        try:
            # Read file content based on extension
            content = ""
            ext = file_path.suffix.lower()
            
            if ext in ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.md', '.yml', '.yaml']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            elif ext in ['.pdf']:
                # For PDF processing, we would use PyPDF2 here
                content = f"[PDF_FILE_CONTENT_{file_path.name}]"
            elif ext in ['.docx']:
                # For DOCX processing, we would use python-docx here
                content = f"[DOCX_FILE_CONTENT_{file_path.name}]"
            else:
                # For unknown formats, try reading as text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
            if not content.strip():
                logger.warning(f"Empty content in file: {file_path}")
                return None
                
            # Preprocess content
            processed_content = self.preprocess_text(content)
            
            # Classify content
            classification = self.classify_text(processed_content)
            
            # Create metadata
            file_info = {
                "source_file": str(file_path),
                "size": file_path.stat().st_size,
                "extension": ext,
                "word_count": len(processed_content.split()),
                "char_count": len(processed_content),
                "classification": classification
            }
            
            # Save classified content
            self.save_classified_content(file_info, processed_content)
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return None
    
    def save_classified_content(self, file_info: Dict, content: str):
        """Save classified content to appropriate directory"""
        category = file_info["classification"]["category"]
        source_path = Path(file_info["source_file"])
        
        # Create subcategories based on content
        if category == "medical":
            if any(keyword in content.lower() for keyword in ["orthopedic", "bone", "joint", "fracture", "muscle", "surgery"]):
                subcategory = "orthopedics"
            else:
                subcategory = "general"
        elif category == "technical":
            if any(keyword in content.lower() for keyword in ["linux", "manjaro", "ubuntu", "server", "sysadmin"]):
                subcategory = "linux"
            elif any(keyword in content.lower() for keyword in ["python", "javascript", "programming", "code", "script"]):
                subcategory = "programming"
            elif any(keyword in content.lower() for keyword in ["docker", "kubernetes", "devops", "ci/cd"]):
                subcategory = "devops"
            else:
                subcategory = "general"
        elif category == "translation":
            if any(lang in content.lower() for lang in ["arabic", "english", "french", "spanish", "translate"]):
                subcategory = "bilingual"
            else:
                subcategory = "general"
        elif category == "reference":
            if any(keyword in content.lower() for keyword in ["manual", "guide", "tutorial", "documentation"]):
                subcategory = "manuals"
            else:
                subcategory = "general"
        else:
            subcategory = "general"
        
        # Create target directory
        target_dir = self.output_dir / "classified" / category / subcategory
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Create output filename
        base_name = source_path.stem
        output_file = target_dir / f"{base_name}_{category}_{subcategory}.md"
        
        # Add metadata header
        metadata_header = f"""---
title: "{base_name}"
category: "{category}"
subcategory: "{subcategory}"
confidence: {file_info['classification']['confidence']}
language: "{file_info['classification']['language']}"
source_file: "{file_info['source_file']}"
size_bytes: {file_info['size']}
word_count: {file_info['word_count']}
char_count: {file_info['char_count']}
classification_timestamp: "{file_info['classification']['timestamp']}"
model_used: "{file_info['classification']['model_used']}"
---

"""
        
        # Write content with metadata
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(metadata_header)
            f.write(content)
            
        logger.info(f"Saved classified content: {output_file}")
    
    def process_directory(self, directory_path: Path) -> List[Dict]:
        """Process all text files in a directory"""
        results = []
        
        # Get all text files
        text_extensions = {'.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.md', '.yml', '.yaml', '.pdf', '.docx'}
        files = []
        
        for root, _, filenames in os.walk(directory_path):
            for filename in filenames:
                if Path(filename).suffix.lower() in text_extensions:
                    files.append(Path(root) / filename)
        
        logger.info(f"Found {len(files)} text files to process")
        
        # Process each file
        for i, file_path in enumerate(files, 1):
            logger.info(f"Processing file {i}/{len(files)}: {file_path}")
            result = self.process_file(file_path)
            if result:
                results.append(result)
                
        # Generate report (without deduplication)
        self.generate_report(results)
        
        return results
    
    def generate_report(self, results: List[Dict]):
        """Generate comprehensive classification report"""
        if not results:
            logger.warning("No results to generate report from")
            return
            
        # Count by category
        category_counts = {}
        language_counts = {}
        total_words = 0
        total_chars = 0
        avg_confidence = 0
        
        for result in results:
            cat = result["classification"]["category"]
            lang = result["classification"]["language"]
            
            category_counts[cat] = category_counts.get(cat, 0) + 1
            language_counts[lang] = language_counts.get(lang, 0) + 1
            total_words += result["word_count"]
            total_chars += result["char_count"]
            avg_confidence += result["classification"]["confidence"]
        
        avg_confidence /= len(results) if results else 0
        
        # Create report
        report_content = f"""# Fast Classification Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Total files processed: {len(results)}
- Total words: {total_words:,}
- Total characters: {total_chars:,}
- Average confidence: {avg_confidence:.1f}%

## Category Distribution
"""
        
        for category, count in sorted(category_counts.items()):
            percentage = (count / len(results)) * 100
            report_content += f"- {category}: {count} ({percentage:.1f}%)\n"
        
        report_content += f"\n## Language Distribution\n"
        for language, count in sorted(language_counts.items()):
            percentage = (count / len(results)) * 100
            report_content += f"- {language}: {count} ({percentage:.1f}%)\n"
        
        # Add file details
        report_content += f"\n## File Details\n"
        for result in results:
            report_content += f"- {result['source_file']} ({result['classification']['category']}, {result['classification']['confidence']}%)\n"
        
        # Save report
        report_file = self.output_dir / "reports" / f"report_fast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Report generated: {report_file}")
        
        # Print summary to console
        print(f"\n{'='*50}")
        print("FAST CLASSIFICATION SUMMARY")
        print(f"{'='*50}")
        print(f"Files processed: {len(results)}")
        print(f"Total words: {total_words:,}")
        print(f"Average confidence: {avg_confidence:.1f}%")
        print(f"Categories: {', '.join(category_counts.keys())}")
        print(f"Languages: {', '.join(language_counts.keys())}")
        print(f"Report saved to: {report_file}")
        print(f"{'='*50}")

def main():
    parser = argparse.ArgumentParser(description="Ultimate Text Classifier - Fast Version")
    parser.add_argument("--input", "-i", type=str, help="Input file or directory path")
    parser.add_argument("--output", "-o", type=str, default="~/classified_ultimate_fast", help="Output directory")
    parser.add_argument("--model", "-m", type=str, default="qwen2.5", help="Ollama model to use")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode instead of GUI")
    
    args = parser.parse_args()
    
    # Initialize classifier
    classifier = UltimateFastClassifier(
        ollama_model=args.model,
        output_dir=args.output
    )
    
    if not args.input:
        print("Ultimate Text Classifier - Fast Version")
        print("="*50)
        print("Options:")
        print("1. Run with GUI (default)")
        print("2. Run with CLI")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            print("GUI mode selected (not implemented in this version)")
            print("Please run with --cli option")
        elif choice == "2":
            input_path = input("Enter input file or directory path: ").strip()
            if not input_path:
                print("No input provided. Exiting.")
                return
            args.input = input_path
            args.cli = True
        else:
            print("Exiting.")
            return
    
    if args.cli:
        input_path = Path(args.input)
        if input_path.is_file():
            print(f"Processing single file: {input_path}")
            result = classifier.process_file(input_path)
            if result:
                print(f"File processed successfully: {result}")
        elif input_path.is_dir():
            print(f"Processing directory: {input_path}")
            results = classifier.process_directory(input_path)
            print(f"Directory processing completed. Results: {len(results)} files processed")
        else:
            print(f"Invalid input path: {input_path}")
            return
    
    # Save user knowledge
    classifier.save_user_knowledge()

if __name__ == "__main__":
    main()