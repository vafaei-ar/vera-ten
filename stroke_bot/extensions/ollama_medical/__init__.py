"""
Ollama Medical Extension

Provides local LLM integration using Ollama for medical conversations.
This extension handles the AI conversation logic for stroke patient assessments.
"""

from .ollama_client import OllamaClient, OllamaConfig
from .medical_llm import MedicalLLM
from .conversation_memory import ConversationMemory

__all__ = [
    'OllamaClient',
    'OllamaConfig',
    'MedicalLLM', 
    'ConversationMemory'
]
