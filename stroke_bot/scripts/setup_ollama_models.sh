#!/bin/bash

# Setup Ollama Models for Stroke Conversation Bot
# This script downloads and configures the necessary Ollama models

set -e

echo "🤖 Setting up Ollama models for stroke conversation bot..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Please install it first:"
    echo "   curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

# Check if Ollama service is running
if ! ollama list &> /dev/null; then
    echo "🔄 Starting Ollama service..."
    ollama serve &
    sleep 5
fi

# Download models (prioritize smaller, efficient models for medical conversations)
echo "📥 Downloading Ollama models..."

# Primary model for medical conversations (smaller, faster)
echo "   - Downloading llama3.2:3b (recommended for medical conversations)..."
ollama pull llama3.2:3b

# Alternative models for different use cases
echo "   - Downloading mistral:7b (alternative option)..."
ollama pull mistral:7b

# Tiny model for testing
echo "   - Downloading phi3:mini (for testing)..."
ollama pull phi3:mini

# Create model configuration
echo "⚙️ Creating model configuration..."

# Ensure config directory exists relative to project root (stroke_bot)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR%/scripts}"
CONFIG_DIR="$PROJECT_ROOT/config"
mkdir -p "$CONFIG_DIR"

cat > "$CONFIG_DIR/ollama_models.json" << EOF
{
  "primary_model": "llama3.2:3b",
  "alternative_models": ["mistral:7b", "phi3:mini"],
  "model_configs": {
    "llama3.2:3b": {
      "temperature": 0.7,
      "top_p": 0.9,
      "max_tokens": 512,
      "context_length": 4096
    },
    "mistral:7b": {
      "temperature": 0.6,
      "top_p": 0.9,
      "max_tokens": 1024,
      "context_length": 8192
    },
    "phi3:mini": {
      "temperature": 0.8,
      "top_p": 0.9,
      "max_tokens": 256,
      "context_length": 2048
    }
  }
}
EOF

echo "✅ Ollama models setup complete!"
echo "📋 Available models:"
ollama list
