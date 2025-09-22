"""
YAML Conversation Parser

Parses the stroke_sen1.yml file and extracts conversation structure,
questions, and flow information.
"""

import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Question:
    """Represents a single question in the conversation flow."""
    key: str
    type: str  # 'free', 'confirm', 'section'
    prompt: str
    on_deny: Optional[str] = None
    section: Optional[str] = None


@dataclass
class ConversationMeta:
    """Metadata about the conversation."""
    organization: str
    service_name: str
    site: str
    version: str
    description: str


@dataclass
class ConversationTemplate:
    """Greeting template with variables."""
    template: str
    variables: List[str]


class YAMLConversationParser:
    """Parses stroke conversation YAML files."""
    
    def __init__(self, yaml_file_path: str):
        """Initialize parser with YAML file path."""
        self.yaml_file_path = Path(yaml_file_path)
        self.data = self._load_yaml()
        
    def _load_yaml(self) -> Dict[str, Any]:
        """Load and parse the YAML file."""
        try:
            with open(self.yaml_file_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"YAML file not found: {self.yaml_file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML file: {e}")
    
    def get_meta(self) -> ConversationMeta:
        """Extract metadata from the YAML file."""
        meta_data = self.data.get('meta', {})
        return ConversationMeta(
            organization=meta_data.get('organization', ''),
            service_name=meta_data.get('service_name', ''),
            site=meta_data.get('site', ''),
            version=meta_data.get('version', ''),
            description=meta_data.get('description', '')
        )
    
    def get_greeting_template(self) -> ConversationTemplate:
        """Extract greeting template and variables."""
        greeting_data = self.data.get('greeting', {})
        return ConversationTemplate(
            template=greeting_data.get('template', ''),
            variables=greeting_data.get('variables', [])
        )
    
    def get_questions(self) -> List[Question]:
        """Extract all questions from the flow section."""
        questions = []
        flow_data = self.data.get('flow', [])
        current_section = None
        
        for item in flow_data:
            if isinstance(item, dict):
                if 'section' in item:
                    current_section = item['section']
                elif 'key' in item:
                    question = Question(
                        key=item['key'],
                        type=item.get('type', 'free'),
                        prompt=item.get('prompt', ''),
                        on_deny=item.get('on_deny'),
                        section=current_section
                    )
                    questions.append(question)
        
        return questions
    
    def get_sections(self) -> List[str]:
        """Get all section names from the conversation flow."""
        sections = []
        flow_data = self.data.get('flow', [])
        
        for item in flow_data:
            if isinstance(item, dict) and 'section' in item:
                sections.append(item['section'])
        
        return sections
    
    def get_wrapup_message(self) -> str:
        """Get the wrap-up message."""
        return self.data.get('wrapup', {}).get('message', '')
    
    def get_emergency_disclaimer(self) -> str:
        """Get the emergency disclaimer."""
        return self.data.get('emergency_disclaimer', '')
    
    def get_stroke_warning_signs(self) -> List[str]:
        """Get the list of stroke warning signs."""
        return self.data.get('stroke_warning_signs', [])
    
    def get_consent_question(self) -> Optional[Question]:
        """Get the consent question specifically."""
        questions = self.get_questions()
        for question in questions:
            if question.key == 'consent':
                return question
        return None
    
    def get_questions_by_section(self, section_name: str) -> List[Question]:
        """Get all questions for a specific section."""
        questions = self.get_questions()
        return [q for q in questions if q.section == section_name]
    
    def get_question_by_key(self, key: str) -> Optional[Question]:
        """Get a specific question by its key."""
        questions = self.get_questions()
        for question in questions:
            if question.key == key:
                return question
        return None
    
    def validate_conversation_structure(self) -> List[str]:
        """Validate the conversation structure and return any issues."""
        issues = []
        
        # Check required sections
        required_sections = ['meta', 'greeting', 'flow', 'wrapup']
        for section in required_sections:
            if section not in self.data:
                issues.append(f"Missing required section: {section}")
        
        # Check for consent question
        consent_question = self.get_consent_question()
        if not consent_question:
            issues.append("Missing consent question")
        
        # Check for at least one question in each section
        sections = self.get_sections()
        for section in sections:
            section_questions = self.get_questions_by_section(section)
            if not section_questions:
                issues.append(f"Section '{section}' has no questions")
        
        return issues
    
    def export_structured_data(self) -> Dict[str, Any]:
        """Export the conversation data in a structured format."""
        return {
            'meta': self.get_meta().__dict__,
            'greeting': self.get_greeting_template().__dict__,
            'sections': self.get_sections(),
            'questions': [q.__dict__ for q in self.get_questions()],
            'wrapup_message': self.get_wrapup_message(),
            'emergency_disclaimer': self.get_emergency_disclaimer(),
            'stroke_warning_signs': self.get_stroke_warning_signs(),
            'validation_issues': self.validate_conversation_structure()
        }
