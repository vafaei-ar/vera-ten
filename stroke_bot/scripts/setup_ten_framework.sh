#!/bin/bash

# Setup TEN Framework Integration
# This script sets up the integration with the existing ten-framework

set -e

echo "🔧 Setting up TEN Framework integration..."

# Resolve paths based on this script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR%/scripts}"
TEN_PATH="${PROJECT_ROOT}/../ten-framework"

# Check if ten-framework exists
if [ ! -d "$TEN_PATH" ]; then
    echo "❌ ten-framework directory not found at: $TEN_PATH"
    echo "   Please ensure the repo contains 'ten-framework' at /home/asadr/works/repos/vera-ten/ten-framework"
    exit 1
fi

# Ensure target dirs exist
mkdir -p "$PROJECT_ROOT/extensions"
mkdir -p "$PROJECT_ROOT/extensions/custom"
mkdir -p "$PROJECT_ROOT/config"

# Create symbolic links to ten-framework components
echo "🔗 Creating symbolic links to ten-framework..."

# Link to ten-framework packages (core)
ln -sf "$TEN_PATH/packages/core_extensions/default_extension_python" "$PROJECT_ROOT/extensions/ten_default_extension"
ln -sf "$TEN_PATH/packages/core_extensions/default_asr_extension_python" "$PROJECT_ROOT/extensions/ten_asr_extension"
ln -sf "$TEN_PATH/packages/core_extensions/default_tts_extension_python" "$PROJECT_ROOT/extensions/ten_tts_extension"

# Create ten-framework configuration
echo "⚙️ Creating ten-framework configuration..."
cat > "$PROJECT_ROOT/config/ten_framework_config.json" << EOF
{
  "ten_framework_path": "$TEN_PATH",
  "extensions": {
    "ollama_medical": "$PROJECT_ROOT/extensions/custom/ollama_medical_python",
    "conversation_flow": "$PROJECT_ROOT/extensions/custom/conversation_flow_python",
    "recording": "$PROJECT_ROOT/extensions/custom/recording_python"
  },
  "runtime": {
    "go_runtime": "$TEN_PATH/ai_agents/agents/bin/ten_runtime_go",
    "log_level": "info"
  }
}
EOF

echo "✅ TEN Framework integration setup complete!"
