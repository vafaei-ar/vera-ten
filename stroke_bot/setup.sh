#!/bin/bash

# Stroke Conversation Bot Setup Script
# This script sets up the complete stroke conversation bot system

set -e

echo "🏥 Setting up Stroke Conversation Bot..."

# Check if conda environment exists
if ! conda env list | grep -q "vten"; then
    echo "❌ Conda environment 'vten' not found. Please create it first:"
    echo "   conda create -n vten python=3.10"
    echo "   conda activate vten"
    exit 1
fi

# Activate conda environment
echo "🔄 Activating conda environment 'vten'..."
eval "$(conda shell.bash hook)"
conda activate vten

# Create project directories
echo "📁 Creating project directories..."
mkdir -p stroke_bot/{extensions,conversation_engine,recording,config,models,data,scripts}

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Download and setup Ollama models
echo "🤖 Setting up Ollama models..."
./scripts/setup_ollama_models.sh

# Setup ten-framework integration
echo "🔧 Setting up ten-framework integration..."
./scripts/setup_ten_framework.sh

# Create configuration files
echo "⚙️ Creating configuration files..."
./scripts/create_configs.sh

# Test installation
echo "🧪 Testing installation..."
python -c "import ollama; print('✅ Ollama integration working')"
python -c "import yaml; print('✅ YAML parsing working')"
python -c "import pyaudio; print('✅ Audio processing working')"

echo "✅ Stroke Conversation Bot setup complete!"
echo ""
echo "🚀 To start the bot:"
echo "   1. conda activate vten"
echo "   2. cd stroke_bot"
echo "   3. python main.py"
echo ""
echo "📋 Available commands:"
echo "   - python main.py --help"
echo "   - python scripts/test_conversation.py"
echo "   - python scripts/export_data.py"
