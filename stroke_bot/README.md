# 🏥 Stroke Conversation Bot

A local AI conversation bot for stroke patient follow-up assessments using Ollama for local LLM processing and real-time voice interaction.

## ✨ Features

- **🤖 Local AI Processing**: Uses Ollama for completely local LLM processing
- **🎙️ Real-time Voice**: Voice conversation with speech-to-text and text-to-speech
- **📋 Structured Assessment**: Follows medical assessment protocols from YAML configuration
- **🔒 Privacy-First**: All processing happens locally, no external API calls
- **📊 Data Export**: Export conversations in JSON, CSV formats
- **🎯 Medical-Focused**: Specialized for stroke patient follow-up care
- **⚡ Real-time Recording**: Automatic conversation recording and transcription

## 🏗️ Architecture

```
stroke_bot/
├── conversation_engine/     # Core conversation logic
│   ├── yaml_parser.py      # Parse stroke_sen1.yml
│   ├── state_machine.py    # Conversation state management
│   ├── prompt_generator.py # Generate AI prompts
│   └── conversation_flow.py # Main flow orchestration
├── extensions/
│   └── ollama_medical/     # Ollama LLM integration
│       ├── ollama_client.py
│       ├── medical_llm.py
│       └── conversation_memory.py
├── recording/              # Audio recording & transcription
│   ├── audio_recorder.py
│   ├── transcriber.py
│   ├── conversation_storage.py
│   └── recording_manager.py
├── config/                 # Configuration files
├── scripts/               # Utility scripts
└── main.py               # Main application
```

## 🚀 Quick Start

### Prerequisites

- **Conda Environment**: `vten` (already created)
- **Ollama**: Installed and running
- **Python 3.10+**: In the conda environment
- **Audio Hardware**: Microphone and speakers

### Installation

1. **Activate the conda environment**:
   ```bash
   conda activate vten
   ```

2. **Run the setup script**:
   ```bash
   cd stroke_bot
   ./setup.sh
   ```

3. **Test the installation**:
   ```bash
   python scripts/test_conversation.py
   ```

### Basic Usage

**Interactive Mode**:
```bash
python main.py --interactive --patient-name "John Doe" --honorific "Mr."
```

**API Mode**:
```bash
python main.py --patient-name "John Doe" --honorific "Mr."
```

## 📋 Usage Examples

### Start a Conversation

```bash
# Interactive mode with a patient
python main.py --interactive --patient-name "Jane Smith" --honorific "Ms."

# Test mode (components only)
python main.py --test
```

### Export Data

```bash
# List recent conversations
python scripts/export_data.py list --limit 20

# Export specific conversation
python scripts/export_data.py conversation <conversation_id> --format json

# Export patient data
python scripts/export_data.py patient "John Doe" --format csv

# Export by date range
python scripts/export_data.py date-range 2024-01-01 2024-01-31 --format json

# Show storage statistics
python scripts/export_data.py stats
```

## ⚙️ Configuration

### Main Configuration

Edit `config/stroke_bot_config.yaml`:

```yaml
bot:
  name: "AI Stroke Navigator"
  organization: "PennState Health"
  site: "Hershey Medical Center"

conversation:
  yaml_file: "../stroke_sen1.yml"
  max_duration_minutes: 30
  emergency_keywords: ["emergency", "911", "urgent", "help"]

llm:
  provider: "ollama"
  model: "llama3.2:3b"
  temperature: 0.7
  max_tokens: 512

audio:
  sample_rate: 16000
  recording_path: "data/recordings"
  transcription_path: "data/transcriptions"
```

### Ollama Models

The setup script automatically downloads recommended models:

- **llama3.2:3b** (recommended for medical conversations)
- **mistral:7b** (alternative option)
- **phi3:mini** (for testing)

## 🎯 Conversation Flow

The bot follows a structured assessment based on `stroke_sen1.yml`:

1. **Greeting & Consent** - Introduction and consent verification
2. **Knowledge Check** - Understanding of ischemic stroke
3. **General Well-Being** - Overall health assessment
4. **Medications** - Medication adherence and side effects
5. **Follow-up Care** - Appointment scheduling and rehabilitation
6. **Lifestyle Management** - Diet, activity, and risk factors
7. **Daily Activities** - ADL support and home safety
8. **Resources** - Support systems and next steps
9. **Wrap-up** - Summary and emergency instructions

## 🔧 Advanced Usage

### Custom Models

Switch to different Ollama models:

```python
from extensions.ollama_medical import MedicalLLM, OllamaConfig

config = OllamaConfig(model="mistral:7b", temperature=0.6)
medical_llm = MedicalLLM(config)
```

### Custom Conversation Flow

Modify `stroke_sen1.yml` to customize the conversation:

```yaml
flow:
  - key: custom_question
    type: free
    prompt: "Your custom question here"
    section: "Custom Section"
```

### Recording Configuration

Adjust audio settings:

```python
from recording import AudioRecorder

recorder = AudioRecorder(
    sample_rate=44100,  # Higher quality
    channels=2,         # Stereo
    chunk_size=2048     # Larger chunks
)
```

## 📊 Data Management

### Storage Structure

```
data/
├── storage/
│   └── conversations.db    # SQLite database
├── recordings/             # Audio files (.wav)
├── transcriptions/         # Text files (.txt)
└── exports/               # Exported data
```

### Database Schema

- **conversations**: Main conversation records
- **responses**: Individual question responses
- **audio_segments**: Audio file segments with timestamps

### Export Formats

- **JSON**: Complete conversation data with metadata
- **CSV**: Tabular format for analysis
- **Excel**: Formatted reports (future)

## 🛠️ Development

### Project Structure

```
stroke_bot/
├── conversation_engine/    # Core conversation logic
├── extensions/            # LLM and external integrations
├── recording/             # Audio and data management
├── config/               # Configuration files
├── scripts/              # Utility and test scripts
├── data/                 # Runtime data storage
└── logs/                 # Application logs
```

### Testing

Run comprehensive tests:

```bash
# Test all components
python scripts/test_conversation.py

# Test specific component
python -c "from conversation_engine import ConversationFlow; print('✅ OK')"
```

### Logging

Logs are written to:
- Console output (INFO level)
- `logs/stroke_bot.log` (DEBUG level)
- `logs/error.log` (ERROR level)

## 🔒 Privacy & Security

- **Local Processing**: All AI processing happens locally
- **No External APIs**: No data sent to external services
- **Encrypted Storage**: Database and files are stored locally
- **HIPAA Compliant**: Designed for healthcare data privacy
- **Audit Trail**: Complete conversation logging

## 🚨 Emergency Handling

The bot automatically detects emergency keywords:

- "emergency", "911", "urgent", "help"
- "chest pain", "can't breathe", "can't speak"
- "numb", "paralyzed", "stroke symptoms"

When detected, the bot immediately:
1. Stops the conversation
2. Provides emergency instructions
3. Logs the emergency event
4. Saves the conversation for review

## 📈 Performance

### System Requirements

- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4GB+ (8GB+ recommended for larger models)
- **Storage**: 10GB+ for models and data
- **Audio**: Microphone and speakers

### Optimization

- Use smaller models (llama3.2:3b) for faster responses
- Adjust audio chunk size for latency vs. quality
- Enable audio compression for storage efficiency

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## 🆘 Support

### Common Issues

**Ollama not responding**:
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve
```

**Audio not working**:
```bash
# Test audio input
python -c "import pyaudio; print('Audio OK')"

# Check microphone permissions
```

**Model not found**:
```bash
# Pull the model
ollama pull llama3.2:3b

# List available models
ollama list
```

### Getting Help

1. Check the logs in `logs/stroke_bot.log`
2. Run the test script: `python scripts/test_conversation.py`
3. Check Ollama status: `ollama list`
4. Verify audio hardware

## 🎉 Success!

You now have a fully functional stroke conversation bot that:

✅ Runs completely locally with Ollama  
✅ Follows medical assessment protocols  
✅ Records and transcribes conversations  
✅ Exports data in multiple formats  
✅ Handles emergency situations  
✅ Maintains patient privacy  

**Ready to start your first conversation!** 🏥🤖
