"""
TEN Framework Integration

Integrates the stroke conversation bot with the TEN framework for real-time
voice interaction and multimodal capabilities.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import subprocess
import time

logger = logging.getLogger(__name__)


class TenFrameworkIntegration:
    """Handles integration with the TEN framework."""
    
    def __init__(self, ten_framework_path: str = "../../ten-framework"):
        """Initialize TEN framework integration."""
        self.ten_framework_path = Path(ten_framework_path)
        self.agent_config = None
        self.manifest_config = None
        self.is_initialized = False
        
        # Check if TEN framework exists
        if not self.ten_framework_path.exists():
            logger.warning(f"TEN framework not found at {ten_framework_path}")
    
    def create_stroke_agent_config(self, 
                                 patient_name: str,
                                 ollama_model: str = "llama3.2:3b",
                                 agora_app_id: str = "",
                                 agora_certificate: str = "",
                                 deepgram_api_key: str = "",
                                 elevenlabs_api_key: str = "") -> bool:
        """Create TEN framework agent configuration for stroke bot."""
        try:
            # Create agent directory
            agent_dir = self.ten_framework_path / "ai_agents" / "agents" / "examples" / "stroke-conversation-bot"
            agent_dir.mkdir(parents=True, exist_ok=True)
            
            # Create manifest.json
            self.manifest_config = {
                "type": "app",
                "name": "stroke_conversation_bot",
                "version": "1.0.0",
                "dependencies": [
                    {
                        "type": "system",
                        "name": "ten_runtime_go",
                        "version": "0.11"
                    },
                    {
                        "type": "extension",
                        "agora_rtc",
                        "version": "=0.23.0-rc2"
                    },
                    {
                        "type": "system",
                        "name": "ten_ai_base",
                        "version": "0.7"
                    }
                ],
                "scripts": {
                    "start": "bin/start"
                }
            }
            
            # Create property.json
            self.agent_config = {
                "ten": {
                    "predefined_graphs": [
                        {
                            "name": "stroke_conversation",
                            "auto_start": True,
                            "graph": {
                                "nodes": [
                                    {
                                        "type": "extension",
                                        "name": "agora_rtc",
                                        "addon": "agora_rtc",
                                        "extension_group": "default",
                                        "property": {
                                            "app_id": agora_app_id,
                                            "app_certificate": agora_certificate,
                                            "channel": "stroke_conversation",
                                            "stream_id": 1234,
                                            "remote_stream_id": 123,
                                            "subscribe_audio": True,
                                            "publish_audio": True,
                                            "publish_data": True,
                                            "enable_agora_asr": False
                                        }
                                    },
                                    {
                                        "type": "extension",
                                        "name": "stt",
                                        "addon": "deepgram_asr_python",
                                        "extension_group": "stt",
                                        "property": {
                                            "params": {
                                                "api_key": deepgram_api_key,
                                                "language": "en-US"
                                            }
                                        }
                                    },
                                    {
                                        "type": "extension",
                                        "name": "llm",
                                        "addon": "ollama_medical_python",
                                        "extension_group": "chatgpt",
                                        "property": {
                                            "model": ollama_model,
                                            "temperature": 0.7,
                                            "max_tokens": 512,
                                            "patient_name": patient_name,
                                            "conversation_type": "stroke_assessment"
                                        }
                                    },
                                    {
                                        "type": "extension",
                                        "name": "tts",
                                        "addon": "elevenlabs_tts2_python",
                                        "extension_group": "tts",
                                        "property": {
                                            "dump": False,
                                            "dump_path": "./",
                                            "params": {
                                                "key": elevenlabs_api_key,
                                                "model_id": "eleven_multilingual_v2",
                                                "voice_id": "pNInz6obpgDQGcFmaJgB",
                                                "output_format": "pcm_16000"
                                            }
                                        }
                                    },
                                    {
                                        "type": "extension",
                                        "name": "conversation_flow",
                                        "addon": "conversation_flow_python",
                                        "extension_group": "control",
                                        "property": {
                                            "yaml_file": "../../stroke_sen1.yml",
                                            "conversation_type": "stroke_assessment"
                                        }
                                    },
                                    {
                                        "type": "extension",
                                        "name": "recording_manager",
                                        "addon": "recording_python",
                                        "extension_group": "transcriber",
                                        "property": {
                                            "storage_dir": "data/storage",
                                            "recording_dir": "data/recordings"
                                        }
                                    },
                                    {
                                        "type": "extension",
                                        "name": "main_control",
                                        "addon": "main_python",
                                        "extension_group": "control",
                                        "property": {
                                            "greeting": f"Good day! I am an AI stroke navigator calling from PennState Health. I understand you recently had an ischemic stroke and received care at Hershey Medical Center. I'm going to ask a few questions to see how you're doing after discharge."
                                        }
                                    }
                                ],
                                "connections": [
                                    {
                                        "extension": "main_control",
                                        "cmd": [
                                            {
                                                "names": ["on_user_joined", "on_user_left"],
                                                "source": [{"extension": "agora_rtc"}]
                                            },
                                            {
                                                "names": ["conversation_start"],
                                                "source": [{"extension": "conversation_flow"}]
                                            }
                                        ],
                                        "data": [
                                            {
                                                "name": "asr_result",
                                                "source": [{"extension": "stt"}]
                                            }
                                        ]
                                    },
                                    {
                                        "extension": "agora_rtc",
                                        "audio_frame": [
                                            {
                                                "name": "pcm_frame",
                                                "dest": [{"extension": "stt"}]
                                            },
                                            {
                                                "name": "pcm_frame",
                                                "source": [{"extension": "tts"}]
                                            }
                                        ],
                                        "data": [
                                            {
                                                "name": "data",
                                                "source": [{"extension": "recording_manager"}]
                                            }
                                        ]
                                    },
                                    {
                                        "extension": "conversation_flow",
                                        "data": [
                                            {
                                                "name": "conversation_state",
                                                "source": [{"extension": "llm"}]
                                            },
                                            {
                                                "name": "patient_response",
                                                "source": [{"extension": "stt"}]
                                            }
                                        ]
                                    },
                                    {
                                        "extension": "llm",
                                        "data": [
                                            {
                                                "name": "ai_response",
                                                "source": [{"extension": "conversation_flow"}]
                                            }
                                        ]
                                    },
                                    {
                                        "extension": "tts",
                                        "data": [
                                            {
                                                "name": "tts_text",
                                                "source": [{"extension": "llm"}]
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    ],
                    "log": {
                        "handlers": [
                            {
                                "matchers": [{"level": "info"}],
                                "formatter": {
                                    "type": "plain",
                                    "colored": True
                                },
                                "emitter": {
                                    "type": "console",
                                    "config": {"stream": "stdout"}
                                }
                            }
                        ]
                    }
                }
            }
            
            # Save configuration files
            manifest_path = agent_dir / "manifest.json"
            property_path = agent_dir / "property.json"
            
            with open(manifest_path, 'w') as f:
                json.dump(self.manifest_config, f, indent=2)
            
            with open(property_path, 'w') as f:
                json.dump(self.agent_config, f, indent=2)
            
            logger.info(f"TEN framework agent configuration created at {agent_dir}")
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to create TEN framework agent config: {e}")
            return False
    
    def create_custom_extensions(self) -> bool:
        """Create custom extensions for the stroke bot."""
        try:
            extensions_dir = self.ten_framework_path / "ai_agents" / "agents" / "ten_packages" / "extension"
            
            # Create ollama_medical_python extension
            ollama_dir = extensions_dir / "ollama_medical_python"
            ollama_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy our Ollama extension
            import shutil
            source_dir = Path(__file__).parent / "ollama_medical"
            if source_dir.exists():
                shutil.copytree(source_dir, ollama_dir / "ollama_medical", dirs_exist_ok=True)
            
            # Create conversation_flow_python extension
            flow_dir = extensions_dir / "conversation_flow_python"
            flow_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy conversation engine
            source_flow_dir = Path(__file__).parent.parent / "conversation_engine"
            if source_flow_dir.exists():
                shutil.copytree(source_flow_dir, flow_dir / "conversation_engine", dirs_exist_ok=True)
            
            # Create recording_python extension
            recording_dir = extensions_dir / "recording_python"
            recording_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy recording module
            source_recording_dir = Path(__file__).parent.parent / "recording"
            if source_recording_dir.exists():
                shutil.copytree(source_recording_dir, recording_dir / "recording", dirs_exist_ok=True)
            
            logger.info("Custom extensions created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create custom extensions: {e}")
            return False
    
    def start_ten_agent(self) -> bool:
        """Start the TEN framework agent."""
        try:
            if not self.is_initialized:
                logger.error("TEN framework not initialized")
                return False
            
            # Change to TEN framework directory
            agent_dir = self.ten_framework_path / "ai_agents" / "agents" / "examples" / "stroke-conversation-bot"
            
            # Start the agent
            cmd = ["task", "use", "AGENT=stroke-conversation-bot"]
            result = subprocess.run(cmd, cwd=agent_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("TEN framework agent started successfully")
                return True
            else:
                logger.error(f"Failed to start TEN framework agent: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting TEN framework agent: {e}")
            return False
    
    def stop_ten_agent(self) -> bool:
        """Stop the TEN framework agent."""
        try:
            # Find and kill the agent process
            cmd = ["pkill", "-f", "stroke-conversation-bot"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            logger.info("TEN framework agent stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping TEN framework agent: {e}")
            return False
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get the status of the TEN framework agent."""
        try:
            # Check if agent is running
            cmd = ["pgrep", "-f", "stroke-conversation-bot"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            is_running = result.returncode == 0
            
            return {
                "is_running": is_running,
                "agent_name": "stroke-conversation-bot",
                "ten_framework_path": str(self.ten_framework_path),
                "initialized": self.is_initialized
            }
            
        except Exception as e:
            logger.error(f"Error checking agent status: {e}")
            return {"is_running": False, "error": str(e)}
    
    def create_launch_script(self) -> bool:
        """Create a launch script for the stroke bot."""
        try:
            script_content = """#!/bin/bash

# Stroke Conversation Bot Launch Script

echo "🏥 Starting Stroke Conversation Bot..."

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate vten

# Check if Ollama is running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "Starting Ollama service..."
    ollama serve &
    sleep 5
fi

# Start the stroke bot
cd "$(dirname "$0")"
python main.py --interactive --patient-name "$1" --honorific "${2:-Mr.}"

echo "Stroke Conversation Bot stopped."
"""
            
            script_path = Path("launch_stroke_bot.sh")
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Make executable
            script_path.chmod(0o755)
            
            logger.info(f"Launch script created: {script_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create launch script: {e}")
            return False
