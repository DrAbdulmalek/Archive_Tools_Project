# 🔥 Ultimate Text Classifier - Complete Guide

## Overview

The Ultimate Text Classifier is an advanced text classification system with semantic deduplication and active learning capabilities. It supports both Arabic and English text classification using local AI models, making it perfect for training AI models on your own hardware.

## 📦 Project Structure

```
ULTIMATE_PROJECT/
├── 🔥 السكريبتات الرئيسية (Python)
│   ├── ultimate_classifier_v3_fixed.py   ✅ النسخة المستقرة (مُصلحة)
│   ├── ultimate_classifier_fast.py       ⚡ نسخة سريعة (بدون إزالة التكرار الدلالي)
│   └── old_ultimate_classifier_v3_fixed.py   (نسخة احتياطية)
│
├── 🚀 مشغلات النظام
│   ├── run_fixed.sh                       🏁 الموصى به (يثبت الخطوط العربية ويشغل)
│   ├── run.sh                             🏁 بديل
│   └── install_arabic_fonts.sh             خطوط العربية (لنظام Manjaro/Linux)
│
├── 📚 التوثيق الشامل
│   ├── README_COMPLETE.md                  📘 دليل كامل
│   ├── QUICKSTART.md                        ⚡ دليل البدء السريع (5 دقائق)
│   ├── API_DOCS.md                          📖 توثيق البرمجة
│   ├── CHANGELOG.md                          📜 سجل التطوير
│   ├── ARABIC_FIX_FINAL.md                   🔧 حل مشاكل العربية
│   ├── PROBLEM_AND_SOLUTION.md                🐛 المشاكل والحلول
│   └── FREE_QUICK_START.md                     🆓 دليل النسخة المجانية (Colab)
│
├── 📓 إصدارات Google Colab (مجانية)
│   ├── COLAB_Free_Edition.ipynb              3 طرق مجانية (HuggingFace, Gemini, Groq)
│   └── COLAB_Classifier.ipynb                 نسخة أساسية
│
├── ⚙️ ملفات الإعدادات
│   ├── requirements.txt                       مكتبات Python
│   └── user_knowledge.json                     ذاكرة التعلم النشط (تُنشأ تلقائياً)
│
├── 🌐 واجهة الويب (Next.js) – ميزة إضافية
│   ├── src/
│   │   ├── app/api/classify/route.ts           تصنيف عبر API
│   │   ├── app/api/extract/route.ts            استخراج معلومات وتنظيم
│   │   ├── lib/file-processor.ts                معالج متقدم للملفات
│   │   ├── lib/text-processor.ts                 معالج نصوص
│   │   └── app/page.tsx                          واجهة مستخدم
│   └── ...
│
└── 📂 نتائج المعالجة (مثال)
    ├── classified_ultimate/classified/         ملفات مصنفة حسب الفئات
    ├── logs/                                    سجلات المعالجة
    └── reports/                                  تقارير شاملة
```

## ✨ Key Features

| الميزة | الوصف | المصدر |
|--------|-------|--------|
| تصنيف متعدد الطبقات | كلمات مفتاحية ← بحث دلالي (تصحيحات المستخدم) ← LLM (Ollama) | Grok |
| التعلم النشط | حفظ تصحيحات المستخدم في user_knowledge.json وتطبيقها تلقائياً | Gemini |
| إزالة التكرار الدلالي | باستخدام FAISS و embeddings (نموذج intfloat/multilingual-e5-large) | Grok |
| دعم العربية والإنجليزية | كشف اللغة، خطوط عربية مثبتة، واجهة بـ RTL | تطوير جديد + Fiinote |
| واجهة رسومية (GUI) | Tkinter مع شريط تقدم حي وسجلات ملونة | تطوير جديد 2026 |
| معالجة دفعية ذكية | تقسيم الملفات الكبيرة، تنظيف، تقييم الجودة | intelligent-processor |
| 4 نماذج AI محلية | qwen2.5 (الافتراضي)، qwen2.5-coder، phi3، llama3.2 | Ollama |
| تقارير مفصلة | Markdown مع إحصائيات وتصنيفات | hybrid-system |
| استخراج معلومات متقدم | (في نسخة الويب) كيانات طبية وتقنية، تواريخ، أرقام، مواضيع، بيانات تدريب | /api/extract |

## 🚀 Installation

### Prerequisites

```bash
# Update system
sudo pacman -Syu

# Install Python 3.10+ (already present by default)
python --version

# Install Ollama
yay -S ollama   # or from official website
sudo systemctl start ollama
sudo systemctl enable ollama

# Download recommended models
ollama pull qwen2.5
ollama pull qwen2.5-coder   # optional
ollama pull phi3            # optional
```

### Setup Python Environment

```bash
cd ULTIMATE_PROJECT

# (Optional) Create virtual environment
python -m venv venv
source venv/bin/activate

# Install basic libraries
pip install -r requirements.txt

# Install advanced libraries (for additional features)
pip install sentence-transformers faiss-cpu chromadb beautifulsoup4 PyPDF2 python-docx --break-system-packages
```

## 🎯 Usage

### Running the System

#### 1. Graphical Interface (Recommended)

```bash
./run_fixed.sh
```

This script will:
- Check Python, Ollama, and models
- Automatically install Arabic fonts (for proper display)
- Show selection menu (choose 1 for interface)

#### 2. Command Line Interface

```bash
python ultimate_classifier_v3_fixed.py --cli /path/to/input_folder \
    --output ~/classified_output \
    --model qwen
```

#### 3. Fast Version (For many files)

```bash
python ultimate_classifier_fast.py --gui
# or
python ultimate_classifier_fast.py --cli /path/to/input_folder
```

## 📁 Processing Outputs (Example from your logs)

```
classified_ultimate/
├── classified/
│   ├── medical/
│   │   └── orthopedics/         ← نصوص طبية (عظام، كسور، مفاصل)
│   ├── technical/
│   │   ├── linux/                ← نصوص تقنية (لينكس، مانجارو)
│   │   ├── programming/          ← برمجة (بايثون، سكريبتات)
│   │   └── devops/               ← دوكر، خوادم
│   ├── translation/
│   │   ├── ocr/                  ← نصوص ثنائية اللغة، OCR
│   │   └── general/
│   ├── reference/                 ← أدلة، فهارس
│   └── misc/                      ← غير مصنف
├── logs/
│   └── processing_20260219_131330.log    ← سجل كامل
└── reports/
    └── report_20260219_131330.md         ← تقرير شامل
```

Each text file is saved with metadata at the top (classification, confidence, source, quality, etc.).

## 🧠 Using Outputs for AI Model Training

You can convert outputs to suitable training formats:

### 1. Convert to JSONL (JSON per line)

```bash
python -c "
import json, glob
for f in glob.glob('classified_ultimate/classified/**/*.md', recursive=True):
    with open(f) as ff:
        lines = ff.read().split('\n')
        # Extract data from header
        # ... and create JSON line
"
```

### 2. Using user_knowledge.json as few-shot examples

This file contains user corrections and can be included in prompts to models.

## 🔧 Troubleshooting (Based on your successful logs)

| Problem | Solution |
|---------|----------|
| Arabic text shows □□□ | Run ./install_arabic_fonts.sh (included in project) |
| Ollama unavailable | sudo systemctl restart ollama or ollama serve & |
| Slow performance or freezing | Use ultimate_classifier_fast.py or reduce BATCH_SIZE in code |
| Error with sentence-transformers | pip install --upgrade sentence-transformers |
| Memory insufficient | Use phi3 model (lighter) or reduce MAX_TEXT_LENGTH |

## 📊 Success Confirmation (From your logs)

```
✅ Found 10 files
✅ Processing files: 9 processed, 1 skipped
✅ Identical duplicates: 0
✅ Semantic deduplication: Completed successfully
✅ Total words: 93620
✅ Quality average: 77%
✅ No errors
```

## 🎯 Summary

The project is production-ready and works efficiently on Manjaro systems with local models. All components are present and documented, and you can:

- Automatically classify thousands of files
- Learn from your corrections to improve accuracy
- Get organized outputs suitable for AI training
- Use GUI or CLI as per your preference

For any queries or modifications, please refer to documentation files inside the ULTIMATE_PROJECT/ folder.