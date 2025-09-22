"""
Ollama Client

Handles communication with the local Ollama service for LLM interactions.
"""

import ollama
import json
import logging
from typing import Dict, List, Optional, Any, Generator
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Configuration for Ollama client."""
    model: str = "llama3.2:3b"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 512
    context_length: int = 4096
    timeout: int = 30


class OllamaClient:
    """Client for interacting with Ollama local LLM service."""
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        """Initialize Ollama client with configuration."""
        self.config = config or OllamaConfig()
        self.client = ollama.Client()
        self._check_ollama_service()
    
    def _check_ollama_service(self) -> None:
        """Check if Ollama service is running and model is available."""
        try:
            # Check if Ollama service is running
            models = self.client.list()
            available_models = [model.model for model in models.models]
            
            if self.config.model not in available_models:
                logger.warning(f"Model {self.config.model} not found. Available models: {available_models}")
                # Try to pull the model
                logger.info(f"Attempting to pull model {self.config.model}...")
                self.client.pull(self.config.model)
            
            logger.info(f"Ollama service connected. Using model: {self.config.model}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Ollama service: {e}")
            raise ConnectionError(f"Cannot connect to Ollama service: {e}")
    
    def generate_response(self, 
                         system_prompt: str, 
                         user_prompt: str, 
                         context: Optional[Dict[str, Any]] = None,
                         stream: bool = False) -> str:
        """Generate a response from the LLM."""
        try:
            # Prepare the conversation messages
            messages = self._prepare_messages(system_prompt, user_prompt, context)
            
            # Generate response
            response = self.client.chat(
                model=self.config.model,
                messages=messages,
                options={
                    'temperature': self.config.temperature,
                    'top_p': self.config.top_p,
                    'num_predict': self.config.max_tokens,
                },
                stream=stream
            )
            
            if stream:
                return self._handle_streaming_response(response)
            else:
                return response['message']['content']
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again."
    
    def generate_streaming_response(self, 
                                  system_prompt: str, 
                                  user_prompt: str, 
                                  context: Optional[Dict[str, Any]] = None) -> Generator[str, None, None]:
        """Generate a streaming response from the LLM."""
        try:
            messages = self._prepare_messages(system_prompt, user_prompt, context)
            
            response = self.client.chat(
                model=self.config.model,
                messages=messages,
                options={
                    'temperature': self.config.temperature,
                    'top_p': self.config.top_p,
                    'num_predict': self.config.max_tokens,
                },
                stream=True
            )
            
            for chunk in response:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
                    
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            yield "I apologize, but I'm experiencing technical difficulties."
    
    def _prepare_messages(self, 
                         system_prompt: str, 
                         user_prompt: str, 
                         context: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Prepare messages for the LLM."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Add context if provided
        if context and context.get('conversation_history'):
            # Add conversation history to context
            history = context['conversation_history']
            for entry in history[-5:]:  # Keep last 5 exchanges
                if entry.get('role') and entry.get('content'):
                    messages.insert(-1, {
                        "role": entry['role'],
                        "content": entry['content']
                    })
        
        return messages
    
    def _handle_streaming_response(self, response) -> str:
        """Handle streaming response and return complete text."""
        full_response = ""
        for chunk in response:
            if 'message' in chunk and 'content' in chunk['message']:
                full_response += chunk['message']['content']
        return full_response
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        try:
            models = self.client.list()
            current_model = next(
                (model for model in models.models if model.model == self.config.model),
                None
            )
            
            if current_model:
                return {
                    'name': current_model.model,
                    'size': getattr(current_model, 'size', 'Unknown'),
                    'modified_at': getattr(current_model, 'modified_at', 'Unknown'),
                    'config': {
                        'temperature': self.config.temperature,
                        'top_p': self.config.top_p,
                        'max_tokens': self.config.max_tokens,
                        'context_length': self.config.context_length
                    }
                }
            else:
                return {'error': f'Model {self.config.model} not found'}
                
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {'error': str(e)}
    
    def test_connection(self) -> bool:
        """Test the connection to Ollama service."""
        try:
            response = self.generate_response(
                system_prompt="You are a helpful assistant.",
                user_prompt="Say 'Hello, I am working correctly.'"
            )
            return "working correctly" in response.lower()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a different model."""
        try:
            # Check if model exists
            models = self.client.list()
            available_models = [model['name'] for model in models['models']]
            
            if model_name not in available_models:
                logger.warning(f"Model {model_name} not found. Attempting to pull...")
                self.client.pull(model_name)
            
            self.config.model = model_name
            logger.info(f"Switched to model: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch model: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        try:
            models = self.client.list()
            return [model.model for model in models.models]
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    def update_config(self, **kwargs) -> None:
        """Update client configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated config: {key} = {value}")
            else:
                logger.warning(f"Unknown config parameter: {key}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the Ollama service."""
        try:
            start_time = time.time()
            response = self.generate_response(
                system_prompt="You are a helpful assistant.",
                user_prompt="Respond with 'OK'"
            )
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'model': self.config.model,
                'response_time': response_time,
                'response': response.strip()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'model': self.config.model
            }
