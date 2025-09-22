"""
Conversation Memory

Manages conversation history and context for the medical LLM.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class ConversationExchange:
    """Represents a single exchange in the conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }


class ConversationMemory:
    """Manages conversation memory and context."""
    
    def __init__(self, max_history: int = 50):
        """Initialize conversation memory."""
        self.max_history = max_history
        self.conversation_history: List[ConversationExchange] = []
        self.patient_context: Dict[str, Any] = {}
        self.medical_context: Dict[str, Any] = {}
        self.start_time: Optional[datetime] = None
    
    def add_exchange(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a conversation exchange to memory."""
        exchange = ConversationExchange(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        self.conversation_history.append(exchange)
        
        # Maintain max history limit
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
        
        # Set start time if this is the first exchange
        if self.start_time is None:
            self.start_time = exchange.timestamp
        
        logger.debug(f"Added {role} exchange to memory")
    
    def get_context(self, max_exchanges: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation context."""
        recent_exchanges = self.conversation_history[-max_exchanges:]
        return [
            {
                'role': exchange.role,
                'content': exchange.content
            }
            for exchange in recent_exchanges
        ]
    
    def get_full_history(self) -> List[Dict[str, Any]]:
        """Get complete conversation history."""
        return [exchange.to_dict() for exchange in self.conversation_history]
    
    def get_exchanges_by_role(self, role: str) -> List[ConversationExchange]:
        """Get all exchanges by a specific role."""
        return [exchange for exchange in self.conversation_history if exchange.role == role]
    
    def get_recent_exchanges(self, minutes: int = 5) -> List[ConversationExchange]:
        """Get exchanges from the last N minutes."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            exchange for exchange in self.conversation_history
            if exchange.timestamp >= cutoff_time
        ]
    
    def get_conversation_duration(self) -> Optional[float]:
        """Get conversation duration in seconds."""
        if self.start_time and self.conversation_history:
            last_exchange = self.conversation_history[-1]
            return (last_exchange.timestamp - self.start_time).total_seconds()
        return None
    
    def get_exchange_count(self) -> int:
        """Get total number of exchanges."""
        return len(self.conversation_history)
    
    def get_user_responses(self) -> List[str]:
        """Get all user responses."""
        return [
            exchange.content for exchange in self.conversation_history
            if exchange.role == 'user'
        ]
    
    def get_assistant_responses(self) -> List[str]:
        """Get all assistant responses."""
        return [
            exchange.content for exchange in self.conversation_history
            if exchange.role == 'assistant'
        ]
    
    def set_patient_context(self, context: Dict[str, Any]) -> None:
        """Set patient-specific context."""
        self.patient_context.update(context)
        logger.debug(f"Updated patient context: {list(context.keys())}")
    
    def get_patient_context(self) -> Dict[str, Any]:
        """Get patient context."""
        return self.patient_context.copy()
    
    def set_medical_context(self, context: Dict[str, Any]) -> None:
        """Set medical context."""
        self.medical_context.update(context)
        logger.debug(f"Updated medical context: {list(context.keys())}")
    
    def get_medical_context(self) -> Dict[str, Any]:
        """Get medical context."""
        return self.medical_context.copy()
    
    def search_exchanges(self, query: str, role: Optional[str] = None) -> List[ConversationExchange]:
        """Search for exchanges containing a query."""
        query_lower = query.lower()
        results = []
        
        for exchange in self.conversation_history:
            if role and exchange.role != role:
                continue
            
            if query_lower in exchange.content.lower():
                results.append(exchange)
        
        return results
    
    def get_keywords_frequency(self) -> Dict[str, int]:
        """Get frequency of keywords in the conversation."""
        keywords = {}
        
        for exchange in self.conversation_history:
            words = exchange.content.lower().split()
            for word in words:
                # Simple word cleaning
                word = word.strip('.,!?;:"()[]{}')
                if len(word) > 3:  # Only count words longer than 3 characters
                    keywords[word] = keywords.get(word, 0) + 1
        
        # Return top 20 most frequent keywords
        return dict(sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:20])
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation."""
        if not self.conversation_history:
            return {"error": "No conversation history"}
        
        user_responses = self.get_user_responses()
        assistant_responses = self.get_assistant_responses()
        
        return {
            "total_exchanges": len(self.conversation_history),
            "user_responses": len(user_responses),
            "assistant_responses": len(assistant_responses),
            "duration_seconds": self.get_conversation_duration(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_exchange_time": self.conversation_history[-1].timestamp.isoformat(),
            "patient_context": self.patient_context,
            "medical_context": self.medical_context,
            "top_keywords": self.get_keywords_frequency()
        }
    
    def export_to_json(self, filepath: str) -> None:
        """Export conversation history to JSON file."""
        data = {
            "conversation_history": self.get_full_history(),
            "patient_context": self.patient_context,
            "medical_context": self.medical_context,
            "summary": self.get_conversation_summary()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Conversation exported to {filepath}")
    
    def load_from_json(self, filepath: str) -> None:
        """Load conversation history from JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load conversation history
            self.conversation_history = []
            for exchange_data in data.get('conversation_history', []):
                exchange = ConversationExchange(
                    role=exchange_data['role'],
                    content=exchange_data['content'],
                    timestamp=datetime.fromisoformat(exchange_data['timestamp']),
                    metadata=exchange_data.get('metadata')
                )
                self.conversation_history.append(exchange)
            
            # Load contexts
            self.patient_context = data.get('patient_context', {})
            self.medical_context = data.get('medical_context', {})
            
            # Set start time
            if self.conversation_history:
                self.start_time = self.conversation_history[0].timestamp
            
            logger.info(f"Conversation loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading conversation from {filepath}: {e}")
            raise
    
    def clear(self) -> None:
        """Clear all conversation memory."""
        self.conversation_history = []
        self.patient_context = {}
        self.medical_context = {}
        self.start_time = None
        logger.info("Conversation memory cleared")
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        return {
            "total_exchanges": len(self.conversation_history),
            "max_history": self.max_history,
            "memory_usage_percent": (len(self.conversation_history) / self.max_history) * 100,
            "oldest_exchange": self.conversation_history[0].timestamp.isoformat() if self.conversation_history else None,
            "newest_exchange": self.conversation_history[-1].timestamp.isoformat() if self.conversation_history else None
        }
