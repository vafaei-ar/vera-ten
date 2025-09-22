"""
Prompt Generator

Generates context-aware prompts for the LLM based on conversation state,
patient responses, and medical conversation requirements.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .yaml_parser import YAMLConversationParser, Question
from .state_machine import ConversationState, ConversationContext

logger = logging.getLogger(__name__)


class PromptGenerator:
    """Generates prompts for medical conversation AI."""
    
    def __init__(self, yaml_parser: YAMLConversationParser):
        """Initialize with YAML parser."""
        self.yaml_parser = yaml_parser
        self.conversation_meta = yaml_parser.get_meta()
        self.greeting_template = yaml_parser.get_greeting_template()
        self.questions = yaml_parser.get_questions()
        self.wrapup_message = yaml_parser.get_wrapup_message()
        self.emergency_disclaimer = yaml_parser.get_emergency_disclaimer()
        self.stroke_warning_signs = yaml_parser.get_stroke_warning_signs()
    
    def generate_system_prompt(self) -> str:
        """Generate the system prompt for the AI assistant."""
        return f"""You are an AI stroke navigator calling from {self.conversation_meta.organization}.
You are conducting a post-discharge stroke care follow-up assessment for a patient who recently had an ischemic stroke.

IMPORTANT GUIDELINES:
1. Be empathetic, professional, and supportive
2. Use clear, simple language appropriate for patients
3. Listen actively and ask follow-up questions when appropriate
4. If the patient mentions emergency symptoms, immediately direct them to call 911
5. Do not provide medical advice - only gather information for the care team
6. Keep responses concise but warm
7. Use the patient's name and appropriate honorific
8. Maintain a conversational, caring tone

EMERGENCY KEYWORDS to watch for:
- "emergency", "911", "urgent", "help"
- "chest pain", "can't breathe", "can't speak"
- "numb", "paralyzed", "stroke symptoms"

If you detect any emergency keywords, immediately respond with: "If you are experiencing a medical emergency, please hang up and call 911 immediately."

CONVERSATION STRUCTURE:
- Start with greeting and consent
- Ask about their understanding of ischemic stroke
- Cover: general well-being, medications, follow-up care, lifestyle, daily activities, resources
- End with wrap-up and emergency instructions

Remember: You cannot answer questions during this call, but you will record any requests for the care team."""
    
    def generate_greeting_prompt(self, context: ConversationContext) -> str:
        """Generate the greeting prompt with patient information."""
        template = self.greeting_template.template
        
        # Replace template variables
        greeting = template.format(
            timeofday=context.time_of_day,
            honorific=context.honorific,
            patient_name=context.patient_name,
            organization=self.conversation_meta.organization,
            site=self.conversation_meta.site
        )
        
        return greeting
    
    def generate_question_prompt(self, question: Question, context: ConversationContext) -> str:
        """Generate a prompt for a specific question."""
        base_prompt = question.prompt
        
        # Add context from previous responses if relevant
        context_info = self._get_relevant_context(question, context)
        
        if context_info:
            return f"{base_prompt}\n\n{context_info}"
        
        return base_prompt
    
    def generate_followup_prompt(self, question: Question, response: str, context: ConversationContext) -> str:
        """Generate a follow-up prompt based on patient response."""
        # Check for emergency keywords first
        if self._detect_emergency_keywords(response):
            return self.emergency_disclaimer
        
        # Generate appropriate follow-up based on question type and response
        if question.type == "confirm":
            if "yes" in response.lower() or "sure" in response.lower() or "okay" in response.lower():
                return "Thank you for your consent. Let's begin with a few questions about your recovery."
            else:
                return question.on_deny or "I understand. We won't proceed with the call."
        
        elif question.type == "free":
            # Generate empathetic follow-up based on response content
            return self._generate_empathetic_followup(question, response)
        
        return "Thank you for sharing that information. Let me ask you about..."
    
    def generate_wrapup_prompt(self, context: ConversationContext) -> str:
        """Generate the wrap-up prompt."""
        wrapup = self.wrapup_message
        
        # Add personalized elements
        if context.patient_name:
            wrapup = wrapup.replace("Thank you", f"Thank you, {context.patient_name}")
        
        return wrapup
    
    def generate_emergency_prompt(self) -> str:
        """Generate emergency response prompt."""
        return f"{self.emergency_disclaimer}\n\nStroke warning signs to watch for:\n" + \
               "\n".join(f"- {sign}" for sign in self.stroke_warning_signs)
    
    def _get_relevant_context(self, question: Question, context: ConversationContext) -> str:
        """Get relevant context from previous responses for the current question."""
        context_parts = []
        
        # Add relevant medical information
        if question.section == "medications" and "meds" in context.responses:
            context_parts.append("Based on your previous responses about medications...")
        
        elif question.section == "followup_care" and "fup" in context.responses:
            context_parts.append("Regarding your follow-up care...")
        
        return " ".join(context_parts)
    
    def _detect_emergency_keywords(self, response: str) -> bool:
        """Detect emergency keywords in patient response."""
        emergency_keywords = [
            "emergency", "911", "urgent", "help", "pain", "chest pain",
            "can't breathe", "can't speak", "numb", "paralyzed", "stroke"
        ]
        
        response_lower = response.lower()
        return any(keyword in response_lower for keyword in emergency_keywords)
    
    def _generate_empathetic_followup(self, question: Question, response: str) -> str:
        """Generate empathetic follow-up based on response content."""
        response_lower = response.lower()
        
        # Check for positive indicators
        if any(word in response_lower for word in ["good", "better", "improving", "fine", "okay"]):
            return "That's wonderful to hear. I'm glad you're doing well."
        
        # Check for concerning indicators
        elif any(word in response_lower for word in ["worse", "bad", "difficult", "struggling", "hard"]):
            return "I understand this has been challenging for you. Can you tell me more about what's been difficult?"
        
        # Check for medication concerns
        elif "medication" in response_lower or "medicine" in response_lower:
            return "I'd like to understand more about your medication experience. Can you share more details?"
        
        # Default empathetic response
        return "Thank you for sharing that with me. That's helpful information for your care team."
    
    def generate_conversation_summary_prompt(self, context: ConversationContext) -> str:
        """Generate a prompt for creating conversation summary."""
        return f"""Please create a professional summary of this stroke patient follow-up conversation.

Patient: {context.patient_name}
Date: {datetime.now().strftime('%Y-%m-%d')}
Duration: {len(context.responses)} questions answered

Key areas covered:
- General well-being
- Medication adherence and side effects
- Follow-up care scheduling
- Lifestyle management
- Daily activities and support needs
- Resource requirements

Please provide a structured summary highlighting:
1. Patient's current condition and concerns
2. Medication adherence status
3. Follow-up care needs
4. Any red flags or urgent concerns
5. Recommended next steps for the care team

Keep the summary concise but comprehensive for healthcare providers."""
    
    def get_question_by_state(self, state: ConversationState) -> Optional[Question]:
        """Get the appropriate question for a given conversation state."""
        state_to_key = {
            ConversationState.CONSENT: "consent",
            ConversationState.KNOWLEDGE_CHECK: "know_ischemic",
            ConversationState.GENERAL_WELLBEING: "general_feeling",
            ConversationState.MEDICATIONS: "meds_pickup",
            ConversationState.FOLLOWUP_CARE: "fup_scheduled",
            ConversationState.LIFESTYLE: "lifestyle_adherence",
            ConversationState.DAILY_ACTIVITIES: "adl_support",
            ConversationState.RESOURCES: "who_to_call"
        }
        
        key = state_to_key.get(state)
        if key:
            return self.yaml_parser.get_question_by_key(key)
        
        return None
