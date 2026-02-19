#!/bin/bash

# Ultimate Text Classifier - Fixed Version Runner
# This script sets up the environment and runs the classifier

echo "🔥 Ultimate Text Classifier - Fixed Version Runner"
echo "================================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.10+"
    exit 1
fi

echo "✅ Python3 is available: $(python3 --version)"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "❌ Ollama is not running. Starting Ollama..."
    if command -v systemctl &> /dev/null; then
        sudo systemctl start ollama
        sleep 3
    elif command -v ollama &> /dev/null; then
        ollama serve &
        sleep 5
    else
        echo "❌ Ollama is not installed. Please install Ollama first."
        exit 1
    fi
else
    echo "✅ Ollama is running"
fi

# Check if required models are available
REQUIRED_MODELS=("qwen2.5" "phi3")
AVAILABLE_MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; data=json.load(sys.stdin); print([m['name'].split(':')[0] for m in data.get('models', [])])")

for model in "${REQUIRED_MODELS[@]}"; do
    if [[ "$AVAILABLE_MODELS" =~ "$model" ]]; then
        echo "✅ Model $model is available"
    else
        echo "⚠️  Model $model is not available. Attempting to pull..."
        ollama pull "$model"
        if [ $? -eq 0 ]; then
            echo "✅ Model $model downloaded successfully"
        else
            echo "❌ Failed to download model $model"
        fi
    fi
done

# Install required Python packages
echo "📦 Installing required Python packages..."
pip install -r requirements.txt

# Install additional packages for better functionality
echo "📦 Installing additional packages..."
pip install sentence-transformers faiss-cpu chromadb beautifulsoup4 PyPDF2 python-docx --break-system-packages

# Run the classifier
echo "🚀 Running Ultimate Text Classifier - Fixed Version..."
python3 scripts/ultimate_classifier_v3_fixed.py "$@"