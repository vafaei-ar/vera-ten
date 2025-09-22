"""
Conversation State Machine

Manages the conversation flow state and transitions between different
phases of the stroke patient assessment.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Possible states in the conversation flow."""
    IDLE = "idle"
    GREETING = "greeting"
    CONSENT = "consent"
    KNOWLEDGE_CHECK = "knowledge_check"
    GENERAL_WELLBEING = "general_wellbeing"
    MEDICATIONS = "medications"
    FOLLOWUP_CARE = "followup_care"
    LIFESTYLE = "lifestyle"
    DAILY_ACTIVITIES = "daily_activities"
    RESOURCES = "resources"
    WRAPUP = "wrapup"
    EMERGENCY_EXIT = "emergency_exit"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ConversationContext:
    """Context information for the conversation."""
    patient_name: str = ""
    honorific: str = ""
    time_of_day: str = ""
    organization: str = ""
    site: str = ""
    start_time: Optional[datetime] = None
    current_question_index: int = 0
    responses: Dict[str, Any] = None
    emergency_detected: bool = False
    
    def __post_init__(self):
        if self.responses is None:
            self.responses = {}
        if self.start_time is None:
            self.start_time = datetime.now()


@dataclass
class StateTransition:
    """Represents a state transition with conditions."""
    from_state: ConversationState
    to_state: ConversationState
    condition: Optional[Callable[[ConversationContext], bool]] = None
    action: Optional[Callable[[ConversationContext], None]] = None


class ConversationStateMachine:
    """Manages conversation state and transitions."""
    
    def __init__(self):
        """Initialize the state machine."""
        self.current_state = ConversationState.IDLE
        self.context = ConversationContext()
        self.transitions = self._create_transitions()
        self.state_history = []
        
    def _create_transitions(self) -> List[StateTransition]:
        """Create the state transition rules."""
        return [
            # Initial flow
            StateTransition(ConversationState.IDLE, ConversationState.GREETING),
            StateTransition(ConversationState.GREETING, ConversationState.CONSENT),
            
            # Consent handling
            StateTransition(
                ConversationState.CONSENT, 
                ConversationState.KNOWLEDGE_CHECK,
                condition=lambda ctx: ctx.responses.get('consent') == 'yes'
            ),
            StateTransition(
                ConversationState.CONSENT,
                ConversationState.EMERGENCY_EXIT,
                condition=lambda ctx: ctx.responses.get('consent') == 'no'
            ),
            
            # Main conversation flow
            StateTransition(ConversationState.KNOWLEDGE_CHECK, ConversationState.GENERAL_WELLBEING),
            StateTransition(ConversationState.GENERAL_WELLBEING, ConversationState.MEDICATIONS),
            StateTransition(ConversationState.MEDICATIONS, ConversationState.FOLLOWUP_CARE),
            StateTransition(ConversationState.FOLLOWUP_CARE, ConversationState.LIFESTYLE),
            StateTransition(ConversationState.LIFESTYLE, ConversationState.DAILY_ACTIVITIES),
            StateTransition(ConversationState.DAILY_ACTIVITIES, ConversationState.RESOURCES),
            StateTransition(ConversationState.RESOURCES, ConversationState.WRAPUP),
            StateTransition(ConversationState.WRAPUP, ConversationState.COMPLETED),
            
            # Emergency handling
            StateTransition(
                ConversationState.GREETING,
                ConversationState.EMERGENCY_EXIT,
                condition=lambda ctx: ctx.emergency_detected
            ),
            StateTransition(
                ConversationState.CONSENT,
                ConversationState.EMERGENCY_EXIT,
                condition=lambda ctx: ctx.emergency_detected
            ),
            StateTransition(
                ConversationState.KNOWLEDGE_CHECK,
                ConversationState.EMERGENCY_EXIT,
                condition=lambda ctx: ctx.emergency_detected
            ),
            StateTransition(
                ConversationState.GENERAL_WELLBEING,
                ConversationState.EMERGENCY_EXIT,
                condition=lambda ctx: ctx.emergency_detected
            ),
            StateTransition(
                ConversationState.MEDICATIONS,
                ConversationState.EMERGENCY_EXIT,
                condition=lambda ctx: ctx.emergency_detected
            ),
            StateTransition(
                ConversationState.FOLLOWUP_CARE,
                ConversationState.EMERGENCY_EXIT,
                condition=lambda ctx: ctx.emergency_detected
            ),
            StateTransition(
                ConversationState.LIFESTYLE,
                ConversationState.EMERGENCY_EXIT,
                condition=lambda ctx: ctx.emergency_detected
            ),
            StateTransition(
                ConversationState.DAILY_ACTIVITIES,
                ConversationState.EMERGENCY_EXIT,
                condition=lambda ctx: ctx.emergency_detected
            ),
            StateTransition(
                ConversationState.RESOURCES,
                ConversationState.EMERGENCY_EXIT,
                condition=lambda ctx: ctx.emergency_detected
            ),
            
            # Error handling
            StateTransition(ConversationState.ERROR, ConversationState.IDLE),
        ]
    
    def start_conversation(self, patient_name: str, honorific: str = "Mr.", 
                          organization: str = "", site: str = "") -> None:
        """Start a new conversation."""
        self.context = ConversationContext(
            patient_name=patient_name,
            honorific=honorific,
            organization=organization,
            site=site,
            time_of_day=self._get_time_of_day()
        )
        self.current_state = ConversationState.GREETING
        self.state_history = [self.current_state]
        logger.info(f"Conversation started for {patient_name}")
    
    def _get_time_of_day(self) -> str:
        """Determine time of day based on current time."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        else:
            return "evening"
    
    def process_response(self, question_key: str, response: str) -> bool:
        """Process a patient response and update state."""
        try:
            # Store the response
            self.context.responses[question_key] = response
            
            # Check for emergency keywords
            if self._detect_emergency(response):
                self.context.emergency_detected = True
                logger.warning(f"Emergency detected in response: {response}")
            
            # Try to transition to next state
            return self._try_transition()
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            self.current_state = ConversationState.ERROR
            return False
    
    def _detect_emergency(self, response: str) -> bool:
        """Detect emergency keywords in the response."""
        emergency_keywords = [
            "emergency", "911", "urgent", "help", "pain", "chest pain",
            "can't breathe", "can't speak", "numb", "paralyzed", "stroke"
        ]
        
        response_lower = response.lower()
        return any(keyword in response_lower for keyword in emergency_keywords)
    
    def _try_transition(self) -> bool:
        """Try to transition to the next state based on current state and context."""
        for transition in self.transitions:
            if (transition.from_state == self.current_state and 
                (transition.condition is None or transition.condition(self.context))):
                
                # Execute transition action if available
                if transition.action:
                    transition.action(self.context)
                
                # Update state
                self.current_state = transition.to_state
                self.state_history.append(self.current_state)
                
                logger.info(f"State transition: {transition.from_state.value} -> {transition.to_state.value}")
                return True
        
        return False
    
    def get_current_state(self) -> ConversationState:
        """Get the current conversation state."""
        return self.current_state
    
    def get_context(self) -> ConversationContext:
        """Get the current conversation context."""
        return self.context
    
    def is_conversation_active(self) -> bool:
        """Check if the conversation is still active."""
        return self.current_state not in [
            ConversationState.COMPLETED, 
            ConversationState.EMERGENCY_EXIT, 
            ConversationState.ERROR
        ]
    
    def is_emergency_exit(self) -> bool:
        """Check if the conversation ended due to emergency."""
        return self.current_state == ConversationState.EMERGENCY_EXIT
    
    def is_completed(self) -> bool:
        """Check if the conversation completed normally."""
        return self.current_state == ConversationState.COMPLETED
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation."""
        duration = None
        if self.context.start_time:
            duration = (datetime.now() - self.context.start_time).total_seconds()
        
        return {
            "patient_name": self.context.patient_name,
            "start_time": self.context.start_time.isoformat() if self.context.start_time else None,
            "duration_seconds": duration,
            "final_state": self.current_state.value,
            "total_responses": len(self.context.responses),
            "emergency_detected": self.context.emergency_detected,
            "state_history": [state.value for state in self.state_history],
            "responses": self.context.responses
        }
    
    def reset(self) -> None:
        """Reset the state machine to initial state."""
        self.current_state = ConversationState.IDLE
        self.context = ConversationContext()
        self.state_history = []
        logger.info("State machine reset")
