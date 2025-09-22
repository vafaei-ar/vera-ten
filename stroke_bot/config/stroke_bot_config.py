"""
Stroke Bot Configuration

Handles loading and managing configuration for the stroke conversation bot.
"""

import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return get_default_config()
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Merge with defaults
        default_config = get_default_config()
        merged_config = merge_configs(default_config, config)
        
        logger.info(f"Configuration loaded from {config_path}")
        return merged_config
        
    except Exception as e:
        logger.error(f"Failed to load config: {e}, using defaults")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    return {
        "bot": {
            "name": "AI Stroke Navigator",
            "organization": "PennState Health",
            "site": "Hershey Medical Center",
            "version": "1.0"
        },
        "conversation": {
            "yaml_file": "../stroke_sen1.yml",
            "max_duration_minutes": 30,
            "timeout_seconds": 10,
            "retry_attempts": 3,
            "emergency_keywords": ["emergency", "911", "urgent", "help"]
        },
        "audio": {
            "sample_rate": 16000,
            "channels": 1,
            "chunk_size": 1024,
            "format": "pcm_16000",
            "recording_path": "data/recordings",
            "transcription_path": "data/transcriptions"
        },
        "llm": {
            "provider": "ollama",
            "model": "llama3.2:3b",
            "temperature": 0.7,
            "max_tokens": 512,
            "context_length": 4096
        },
        "storage": {
            "database_path": "data/conversations.db",
            "export_formats": ["json", "csv", "xlsx"],
            "backup_enabled": True,
            "backup_interval_hours": 24
        },
        "logging": {
            "level": "INFO",
            "file_path": "logs/stroke_bot.log",
            "max_file_size_mb": 10,
            "backup_count": 5
        }
    }


def merge_configs(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Merge user configuration with defaults."""
    result = default.copy()
    
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """Save configuration to YAML file."""
    try:
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False


def validate_config(config: Dict[str, Any]) -> list:
    """Validate configuration and return any issues."""
    issues = []
    
    # Check required sections
    required_sections = ["bot", "conversation", "audio", "llm", "storage"]
    for section in required_sections:
        if section not in config:
            issues.append(f"Missing required section: {section}")
    
    # Check bot configuration
    bot_config = config.get("bot", {})
    if not bot_config.get("name"):
        issues.append("Bot name is required")
    
    # Check conversation configuration
    conv_config = config.get("conversation", {})
    if not conv_config.get("yaml_file"):
        issues.append("Conversation YAML file is required")
    
    # Check audio configuration
    audio_config = config.get("audio", {})
    if not audio_config.get("sample_rate"):
        issues.append("Audio sample rate is required")
    
    # Check LLM configuration
    llm_config = config.get("llm", {})
    if not llm_config.get("model"):
        issues.append("LLM model is required")
    
    return issues


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """Get configuration value using dot notation."""
    keys = key_path.split('.')
    value = config
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def set_config_value(config: Dict[str, Any], key_path: str, value: Any) -> bool:
    """Set configuration value using dot notation."""
    keys = key_path.split('.')
    current = config
    
    try:
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return True
    except (KeyError, TypeError):
        return False
