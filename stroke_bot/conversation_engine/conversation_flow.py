"""
Conversation Flow Manager

Orchestrates the entire conversation flow, integrating the YAML parser,
state machine, and prompt generator to manage the stroke patient assessment.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json

from .yaml_parser import YAMLConversationParser, Question
from .state_machine import ConversationStateMachine, ConversationState, ConversationContext
from .prompt_generator import PromptGenerator

logger = logging.getLogger(__name__)


class ConversationFlow:
    """Manages the complete conversation flow for stroke patient assessment."""
    
    def __init__(self, yaml_file_path: str, llm_callback: Optional[Callable] = None):
        """Initialize conversation flow with YAML file and LLM callback."""
        self.yaml_parser = YAMLConversationParser(yaml_file_path)
        self.state_machine = ConversationStateMachine()
        self.prompt_generator = PromptGenerator(self.yaml_parser)
        self.llm_callback = llm_callback
        self.conversation_log = []
        
        # Validate conversation structure
        validation_issues = self.yaml_parser.validate_conversation_structure()
        if validation_issues:
            logger.warning(f"Conversation structure validation issues: {validation_issues}")
    
    def start_conversation(self, patient_name: str, honorific: str = "Mr.", 
                          organization: str = "", site: str = "") -> str:
        """Start a new conversation and return the initial greeting."""
        try:
            # Start the state machine
            self.state_machine.start_conversation(
                patient_name=patient_name,
                honorific=honorific,
                organization=organization or self.yaml_parser.get_meta().organization,
                site=site or self.yaml_parser.get_meta().site
            )
            
            # Generate greeting
            greeting = self.prompt_generator.generate_greeting_prompt(
                self.state_machine.get_context()
            )
            
            # Log the conversation start
            self._log_conversation_event("conversation_started", {
                "patient_name": patient_name,
                "greeting": greeting
            })
            
            return greeting
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            self.state_machine.current_state = ConversationState.ERROR
            return "I apologize, but I'm experiencing technical difficulties. Please try again later."
    
    def process_patient_response(self, response: str) -> str:
        """Process patient response and return AI response."""
        try:
            current_state = self.state_machine.get_current_state()
            context = self.state_machine.get_context()
            
            # Log the patient response
            self._log_conversation_event("patient_response", {
                "state": current_state.value,
                "response": response
            })
            
            # Get current question
            current_question = self.prompt_generator.get_question_by_state(current_state)
            
            if current_question:
                # Process the response through state machine
                question_key = current_question.key
                success = self.state_machine.process_response(question_key, response)
                
                if not success:
                    logger.warning(f"Failed to process response for question: {question_key}")
                    return "I'm sorry, I didn't quite catch that. Could you please repeat your response?"
                
                # Generate appropriate response based on new state
                return self._generate_state_response()
            
            else:
                # Handle special states
                return self._handle_special_state(current_state, response)
                
        except Exception as e:
            logger.error(f"Error processing patient response: {e}")
            return "I apologize for the technical difficulty. Let me try to continue our conversation."
    
    def _generate_state_response(self) -> str:
        """Generate response based on current conversation state."""
        current_state = self.state_machine.get_current_state()
        context = self.state_machine.get_context()
        
        if current_state == ConversationState.EMERGENCY_EXIT:
            return self.prompt_generator.generate_emergency_prompt()
        
        elif current_state == ConversationState.WRAPUP:
            return self.prompt_generator.generate_wrapup_prompt(context)
        
        elif current_state == ConversationState.COMPLETED:
            return "Thank you for completing the assessment. Have a great day!"
        
        elif current_state == ConversationState.ERROR:
            return "I apologize for the technical difficulty. Please try again later."
        
        else:
            # Get the current question
            current_question = self.prompt_generator.get_question_by_state(current_state)
            
            if current_question:
                # Generate the question prompt
                question_prompt = self.prompt_generator.generate_question_prompt(
                    current_question, context
                )
                
                # If we have an LLM callback, use it to generate a more natural response
                if self.llm_callback:
                    try:
                        system_prompt = self.prompt_generator.generate_system_prompt()
                        llm_response = self.llm_callback(
                            system_prompt=system_prompt,
                            user_prompt=question_prompt,
                            context=context
                        )
                        return llm_response
                    except Exception as e:
                        logger.warning(f"LLM callback failed: {e}, using direct prompt")
                
                return question_prompt
            
            return "Let me ask you about your recovery..."
    
    def _handle_special_state(self, state: ConversationState, response: str) -> str:
        """Handle special conversation states."""
        if state == ConversationState.GREETING:
            # Move to consent after greeting
            self.state_machine._try_transition()
            consent_question = self.yaml_parser.get_consent_question()
            if consent_question:
                return consent_question.prompt
        
        elif state == ConversationState.IDLE:
            return "Let me start by greeting you..."
        
        return "I'm not sure how to respond to that. Let me continue with our assessment."
    
    def get_conversation_status(self) -> Dict[str, Any]:
        """Get current conversation status."""
        context = self.state_machine.get_context()
        return {
            "current_state": self.state_machine.get_current_state().value,
            "is_active": self.state_machine.is_conversation_active(),
            "is_emergency": self.state_machine.is_emergency_exit(),
            "is_completed": self.state_machine.is_completed(),
            "patient_name": context.patient_name,
            "responses_count": len(context.responses),
            "conversation_duration": self._get_conversation_duration()
        }
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a complete summary of the conversation."""
        summary = self.state_machine.get_conversation_summary()
        summary["conversation_log"] = self.conversation_log
        summary["validation_issues"] = self.yaml_parser.validate_conversation_structure()
        return summary
    
    def export_conversation_data(self, format: str = "json") -> str:
        """Export conversation data in specified format."""
        summary = self.get_conversation_summary()
        
        if format.lower() == "json":
            return json.dumps(summary, indent=2, default=str)
        elif format.lower() == "csv":
            return self._export_to_csv(summary)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_to_csv(self, summary: Dict[str, Any]) -> str:
        """Export conversation data to CSV format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(["Question", "Response", "Timestamp", "State"])
        
        # Write responses
        for question_key, response in summary.get("responses", {}).items():
            writer.writerow([question_key, response, "", ""])
        
        return output.getvalue()
    
    def _get_conversation_duration(self) -> Optional[float]:
        """Get conversation duration in seconds."""
        context = self.state_machine.get_context()
        if context.start_time:
            return (datetime.now() - context.start_time).total_seconds()
        return None
    
    def _log_conversation_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log a conversation event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        self.conversation_log.append(event)
        logger.debug(f"Conversation event: {event_type}")
    
    def reset_conversation(self) -> None:
        """Reset the conversation to initial state."""
        self.state_machine.reset()
        self.conversation_log = []
        logger.info("Conversation reset")
    
    def get_available_questions(self) -> List[Dict[str, Any]]:
        """Get list of all available questions."""
        questions = self.yaml_parser.get_questions()
        return [
            {
                "key": q.key,
                "type": q.type,
                "prompt": q.prompt,
                "section": q.section
            }
            for q in questions
        ]
    
    def get_questions_by_section(self, section_name: str) -> List[Dict[str, Any]]:
        """Get questions for a specific section."""
        questions = self.yaml_parser.get_questions_by_section(section_name)
        return [
            {
                "key": q.key,
                "type": q.type,
                "prompt": q.prompt,
                "section": q.section
            }
            for q in questions
        ]
    
    def validate_conversation_data(self) -> List[str]:
        """Validate the current conversation data."""
        issues = []
        
        # Check if conversation has started
        if not self.state_machine.get_context().patient_name:
            issues.append("Conversation has not been started")
        
        # Check for required responses
        required_questions = ["consent"]
        for question_key in required_questions:
            if question_key not in self.state_machine.get_context().responses:
                issues.append(f"Missing required response: {question_key}")
        
        # Check for emergency detection
        if self.state_machine.is_emergency_exit():
            issues.append("Conversation ended due to emergency detection")
        
        return issues
