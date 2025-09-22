"""
Medical LLM

Specialized LLM wrapper for medical conversations with context awareness,
emergency detection, and medical conversation best practices.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json

from .ollama_client import OllamaClient, OllamaConfig
from .conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)


class MedicalLLM:
    """Specialized LLM for medical conversations."""
    
    def __init__(self, ollama_config: Optional[OllamaConfig] = None):
        """Initialize medical LLM with Ollama client."""
        self.ollama_client = OllamaClient(ollama_config)
        self.memory = ConversationMemory()
        self.emergency_keywords = [
            "emergency", "911", "urgent", "help", "pain", "chest pain",
            "can't breathe", "can't speak", "numb", "paralyzed", "stroke",
            "heart attack", "severe", "critical", "dying", "unconscious"
        ]
        
        # Medical conversation guidelines
        self.medical_guidelines = self._load_medical_guidelines()
    
    def _load_medical_guidelines(self) -> Dict[str, Any]:
        """Load medical conversation guidelines."""
        return {
            "empathy_keywords": [
                "understand", "difficult", "challenging", "frustrating",
                "scary", "worried", "concerned", "anxious"
            ],
            "reassurance_phrases": [
                "I understand this must be difficult",
                "That sounds challenging",
                "I can imagine how frustrating that must be",
                "It's completely normal to feel that way"
            ],
            "medical_terminology": {
                "ischemic stroke": "a type of stroke caused by a blood clot",
                "medication adherence": "taking medications as prescribed",
                "follow-up care": "ongoing medical appointments",
                "rehabilitation": "therapy to help with recovery"
            }
        }
    
    def generate_medical_response(self, 
                                system_prompt: str, 
                                user_prompt: str, 
                                context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a medical conversation response."""
        try:
            # Check for emergency keywords first
            if self._detect_emergency(user_prompt):
                return self._generate_emergency_response()
            
            # Enhance prompts with medical context
            enhanced_system_prompt = self._enhance_system_prompt(system_prompt, context)
            enhanced_user_prompt = self._enhance_user_prompt(user_prompt, context)
            
            # Add conversation memory
            memory_context = self.memory.get_context()
            if memory_context:
                context = context or {}
                context['conversation_history'] = memory_context
            
            # Generate response
            response = self.ollama_client.generate_response(
                system_prompt=enhanced_system_prompt,
                user_prompt=enhanced_user_prompt,
                context=context
            )
            
            # Post-process response for medical appropriateness
            processed_response = self._post_process_response(response, context)
            
            # Store in memory
            self.memory.add_exchange("user", user_prompt)
            self.memory.add_exchange("assistant", processed_response)
            
            return processed_response
            
        except Exception as e:
            logger.error(f"Error generating medical response: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again."
    
    def generate_streaming_medical_response(self, 
                                          system_prompt: str, 
                                          user_prompt: str, 
                                          context: Optional[Dict[str, Any]] = None):
        """Generate a streaming medical conversation response."""
        try:
            # Check for emergency keywords
            if self._detect_emergency(user_prompt):
                yield self._generate_emergency_response()
                return
            
            # Enhance prompts
            enhanced_system_prompt = self._enhance_system_prompt(system_prompt, context)
            enhanced_user_prompt = self._enhance_user_prompt(user_prompt, context)
            
            # Add memory context
            memory_context = self.memory.get_context()
            if memory_context:
                context = context or {}
                context['conversation_history'] = memory_context
            
            # Generate streaming response
            full_response = ""
            for chunk in self.ollama_client.generate_streaming_response(
                system_prompt=enhanced_system_prompt,
                user_prompt=enhanced_user_prompt,
                context=context
            ):
                full_response += chunk
                yield chunk
            
            # Store complete response in memory
            self.memory.add_exchange("user", user_prompt)
            self.memory.add_exchange("assistant", full_response)
            
        except Exception as e:
            logger.error(f"Error generating streaming medical response: {e}")
            yield "I apologize, but I'm experiencing technical difficulties."
    
    def _detect_emergency(self, text: str) -> bool:
        """Detect emergency keywords in the text."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.emergency_keywords)
    
    def _generate_emergency_response(self) -> str:
        """Generate emergency response."""
        return """If you are experiencing a medical emergency or new stroke symptoms right now, 
please hang up and call 911 immediately.

Stroke warning signs include:
- Sudden weakness or numbness in face, arm, or leg, especially on one side
- Sudden confusion or trouble speaking or understanding speech
- Sudden trouble seeing in one or both eyes
- Sudden severe headache with no known cause
- Sudden trouble walking, dizziness, or loss of balance

Please call 911 immediately if you experience any of these symptoms."""
    
    def _enhance_system_prompt(self, system_prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Enhance system prompt with medical conversation guidelines."""
        medical_guidelines = """
MEDICAL CONVERSATION GUIDELINES:
1. Always maintain a caring, empathetic tone
2. Use simple, clear language appropriate for patients
3. Show understanding and validation of patient concerns
4. Never provide medical advice - only gather information
5. If emergency keywords are detected, immediately direct to 911
6. Use medical terminology appropriately but explain when needed
7. Be supportive and encouraging about recovery
8. Ask follow-up questions to gather complete information
9. Validate patient experiences and feelings
10. Keep responses concise but warm and personal

EMPATHY RESPONSES:
- Acknowledge patient's feelings: "I understand this must be difficult for you"
- Validate concerns: "That's a valid concern"
- Show support: "I'm here to help you through this"
- Encourage: "It sounds like you're making good progress"

MEDICAL TERMINOLOGY EXPLANATIONS:
- Ischemic stroke: a type of stroke caused by a blood clot blocking blood flow to the brain
- Medication adherence: taking your medications exactly as prescribed
- Follow-up care: ongoing appointments with your healthcare team
- Rehabilitation: therapy to help you recover and regain function
"""
        
        return f"{system_prompt}\n\n{medical_guidelines}"
    
    def _enhance_user_prompt(self, user_prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Enhance user prompt with medical context."""
        if not context:
            return user_prompt
        
        # Add patient information if available
        context_info = []
        if context.get('patient_name'):
            context_info.append(f"Patient: {context['patient_name']}")
        if context.get('time_of_day'):
            context_info.append(f"Time: {context['time_of_day']}")
        if context.get('organization'):
            context_info.append(f"Organization: {context['organization']}")
        
        if context_info:
            context_str = " | ".join(context_info)
            return f"[Context: {context_str}] {user_prompt}"
        
        return user_prompt
    
    def _post_process_response(self, response: str, context: Optional[Dict[str, Any]]) -> str:
        """Post-process response for medical appropriateness."""
        # Remove any potential medical advice
        response = self._remove_medical_advice(response)
        
        # Add empathy if response seems too clinical
        response = self._add_empathy_if_needed(response)
        
        # Ensure appropriate length
        response = self._ensure_appropriate_length(response)
        
        return response
    
    def _remove_medical_advice(self, response: str) -> str:
        """Remove any potential medical advice from response."""
        advice_phrases = [
            "you should", "you need to", "you must", "I recommend",
            "take this medication", "stop taking", "change your"
        ]
        
        response_lower = response.lower()
        for phrase in advice_phrases:
            if phrase in response_lower:
                response = response.replace(phrase, "your healthcare team may suggest")
        
        return response
    
    def _add_empathy_if_needed(self, response: str) -> str:
        """Add empathy if response seems too clinical."""
        clinical_indicators = ["patient", "assessment", "evaluation", "clinical"]
        response_lower = response.lower()
        
        if any(indicator in response_lower for indicator in clinical_indicators):
            if not any(empathy in response_lower for empathy in ["understand", "difficult", "challenging"]):
                response = f"I understand this can be challenging. {response}"
        
        return response
    
    def _ensure_appropriate_length(self, response: str) -> str:
        """Ensure response is appropriate length for conversation."""
        # If too long, truncate and add continuation
        if len(response) > 500:
            response = response[:500] + "... Let me know if you'd like me to continue."
        
        # If too short, add encouragement
        elif len(response) < 20:
            response = f"{response} Please feel free to share more details."
        
        return response
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of the conversation."""
        return {
            "total_exchanges": len(self.memory.conversation_history),
            "emergency_detected": any(
                self._detect_emergency(exchange['content']) 
                for exchange in self.memory.conversation_history
            ),
            "conversation_duration": self.memory.get_conversation_duration(),
            "memory_context": self.memory.get_context()
        }
    
    def clear_memory(self) -> None:
        """Clear conversation memory."""
        self.memory.clear()
        logger.info("Conversation memory cleared")
    
    def update_emergency_keywords(self, keywords: List[str]) -> None:
        """Update emergency keywords list."""
        self.emergency_keywords.extend(keywords)
        self.emergency_keywords = list(set(self.emergency_keywords))  # Remove duplicates
        logger.info(f"Updated emergency keywords: {len(self.emergency_keywords)} total")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the medical LLM."""
        ollama_health = self.ollama_client.health_check()
        
        return {
            "ollama_client": ollama_health,
            "memory_status": "active" if self.memory else "inactive",
            "emergency_keywords_count": len(self.emergency_keywords),
            "overall_status": "healthy" if ollama_health.get('status') == 'healthy' else "unhealthy"
        }
