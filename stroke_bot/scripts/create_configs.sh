#!/bin/bash

# Create Configuration Files
# This script creates all necessary configuration files for the stroke bot

set -e

echo "⚙️ Creating configuration files..."

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR%/scripts}"
CONFIG_DIR="$PROJECT_ROOT/config"
DATA_DIR="$PROJECT_ROOT/data"
LOG_DIR="$PROJECT_ROOT/logs"

# Ensure directories exist
mkdir -p "$CONFIG_DIR" "$DATA_DIR/recordings" "$DATA_DIR/transcriptions" "$DATA_DIR/conversations" "$DATA_DIR/exports" "$DATA_DIR/backups" "$LOG_DIR"

# Create main configuration
cat > "$CONFIG_DIR/stroke_bot_config.yaml" << 'EOF'
# Stroke Conversation Bot Configuration

# Bot Settings
bot:
  name: "AI Stroke Navigator"
  organization: "PennState Health"
  site: "Hershey Medical Center"
  version: "1.0"

# Conversation Settings
conversation:
  max_duration_minutes: 30
  timeout_seconds: 10
  retry_attempts: 3
  emergency_keywords: ["emergency", "911", "urgent", "help"]

# Audio Settings
audio:
  sample_rate: 16000
  channels: 1
  chunk_size: 1024
  format: "pcm_16000"
  recording_path: "data/recordings"
  transcription_path: "data/transcriptions"

# LLM Settings
llm:
  provider: "ollama"
  model: "llama3.2:3b"
  temperature: 0.7
  max_tokens: 512
  context_length: 4096

# Data Storage
storage:
  database_path: "data/conversations.db"
  export_formats: ["json", "csv", "xlsx"]
  backup_enabled: true
  backup_interval_hours: 24

# Logging
logging:
  level: "INFO"
  file_path: "logs/stroke_bot.log"
  max_file_size_mb: 10
  backup_count: 5
EOF

# Create conversation flow configuration
cat > "$CONFIG_DIR/conversation_flow.yaml" << 'EOF'
# Conversation Flow Configuration

# Flow States
states:
  - greeting
  - consent
  - knowledge_check
  - general_wellbeing
  - medications
  - followup_care
  - lifestyle
  - daily_activities
  - resources
  - wrapup

# Transitions
transitions:
  greeting:
    next: consent
    conditions: []
  
  consent:
    next: knowledge_check
    conditions:
      - type: "confirmed"
        action: "proceed"
      - type: "denied"
        action: "emergency_exit"
  
  knowledge_check:
    next: general_wellbeing
    conditions: []
  
  general_wellbeing:
    next: medications
    conditions: []
  
  medications:
    next: followup_care
    conditions: []
  
  followup_care:
    next: lifestyle
    conditions: []
  
  lifestyle:
    next: daily_activities
    conditions: []
  
  daily_activities:
    next: resources
    conditions: []
  
  resources:
    next: wrapup
    conditions: []
  
  wrapup:
    next: "end"
    conditions: []

# Emergency handling
emergency:
  keywords: ["emergency", "911", "urgent", "help", "pain", "chest pain"]
  action: "immediate_exit"
  message: "If you are experiencing a medical emergency, please hang up and call 911 immediately."
EOF

# Create logging configuration
cat > "$CONFIG_DIR/logging.yaml" << 'EOF'
# Logging Configuration

version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  detailed:
    format: '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: logs/stroke_bot.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: logs/error.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  stroke_bot:
    level: DEBUG
    handlers: [console, file, error_file]
    propagate: false

  ollama:
    level: INFO
    handlers: [console, file]
    propagate: false

  conversation:
    level: DEBUG
    handlers: [console, file]
    propagate: false

root:
  level: INFO
  handlers: [console, file]
EOF
echo "✅ Configuration files created successfully!"
