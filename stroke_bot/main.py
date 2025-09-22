#!/usr/bin/env python3
"""
Stroke Conversation Bot - Main Application

A local AI conversation bot for stroke patient follow-up assessments
using Ollama for local LLM processing and real-time voice interaction.
"""

import argparse
import logging
import sys
import signal
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from conversation_engine import ConversationFlow
from extensions.ollama_medical import MedicalLLM, OllamaConfig
from recording import RecordingManager
from config.stroke_bot_config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/stroke_bot.log')
    ]
)

logger = logging.getLogger(__name__)


class StrokeConversationBot:
    """Main application class for the stroke conversation bot."""
    
    def __init__(self, config_path: str = "config/stroke_bot_config.yaml"):
        """Initialize the stroke conversation bot."""
        self.config = load_config(config_path)
        self.recording_manager = None
        self.conversation_flow = None
        self.medical_llm = None
        self.is_running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Stroke Conversation Bot initialized")
    
    def initialize(self) -> bool:
        """Initialize all components."""
        try:
            # Load conversation flow
            yaml_file = self.config.get('conversation', {}).get('yaml_file', '../stroke_sen1.yml')
            self.conversation_flow = ConversationFlow(yaml_file)
            
            # Initialize medical LLM
            ollama_config = OllamaConfig(
                model=self.config.get('llm', {}).get('model', 'llama3.2:3b'),
                temperature=self.config.get('llm', {}).get('temperature', 0.7),
                max_tokens=self.config.get('llm', {}).get('max_tokens', 512)
            )
            self.medical_llm = MedicalLLM(ollama_config)
            
            # Initialize recording manager
            self.recording_manager = RecordingManager(
                storage_dir=self.config.get('storage', {}).get('database_path', 'data/storage'),
                recording_dir=self.config.get('audio', {}).get('recording_path', 'data/recordings'),
                transcription_dir=self.config.get('audio', {}).get('transcription_path', 'data/transcriptions')
            )
            
            # Setup callbacks
            self._setup_callbacks()
            
            # Test components
            if not self._test_components():
                return False
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            return False
    
    def _setup_callbacks(self) -> None:
        """Setup callbacks for recording manager."""
        self.recording_manager.set_callbacks(
            on_recording_start=self._on_recording_start,
            on_recording_stop=self._on_recording_stop,
            on_transcription=self._on_transcription,
            on_conversation_saved=self._on_conversation_saved
        )
    
    def _test_components(self) -> bool:
        """Test all components."""
        try:
            # Test Ollama connection
            if not self.medical_llm.ollama_client.test_connection():
                logger.error("Ollama connection test failed")
                return False
            
            # Test transcriber
            if not self.recording_manager.transcriber.test_recognition():
                logger.warning("Transcriber test failed, but continuing...")
            
            logger.info("Component tests completed")
            return True
            
        except Exception as e:
            logger.error(f"Component test failed: {e}")
            return False
    
    def start_conversation(self, patient_name: str, honorific: str = "Mr.") -> bool:
        """Start a new conversation with a patient."""
        try:
            if self.is_running:
                logger.warning("Conversation already in progress")
                return False
            
            # Start recording
            conversation_id = self.recording_manager.start_conversation_recording(
                patient_name=patient_name,
                metadata={
                    "honorific": honorific,
                    "start_time": datetime.now().isoformat()
                }
            )
            
            if not conversation_id:
                logger.error("Failed to start conversation recording")
                return False
            
            # Start conversation flow
            greeting = self.conversation_flow.start_conversation(
                patient_name=patient_name,
                honorific=honorific,
                organization=self.config.get('bot', {}).get('organization', ''),
                site=self.config.get('bot', {}).get('site', '')
            )
            
            # Generate AI response using medical LLM
            ai_response = self.medical_llm.generate_medical_response(
                system_prompt=self.conversation_flow.prompt_generator.generate_system_prompt(),
                user_prompt=greeting,
                context=self.conversation_flow.state_machine.get_context()
            )
            
            self.is_running = True
            logger.info(f"Conversation started with {patient_name}")
            
            # Print initial response
            print(f"\n🤖 AI: {ai_response}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start conversation: {e}")
            return False
    
    def process_patient_input(self, user_input: str) -> Optional[str]:
        """Process patient input and return AI response."""
        try:
            if not self.is_running:
                logger.warning("No active conversation")
                return None
            
            # Process through conversation flow
            flow_response = self.conversation_flow.process_patient_response(user_input)
            
            # Generate AI response using medical LLM
            ai_response = self.medical_llm.generate_medical_response(
                system_prompt=self.conversation_flow.prompt_generator.generate_system_prompt(),
                user_prompt=flow_response,
                context=self.conversation_flow.state_machine.get_context()
            )
            
            # Add response to recording manager
            current_question = self.conversation_flow.prompt_generator.get_question_by_state(
                self.conversation_flow.state_machine.get_current_state()
            )
            
            if current_question:
                self.recording_manager.add_conversation_response(
                    question_key=current_question.key,
                    question_text=current_question.prompt,
                    response_text=user_input,
                    section=current_question.section
                )
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Failed to process patient input: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again."
    
    def end_conversation(self) -> Optional[Dict[str, Any]]:
        """End the current conversation."""
        try:
            if not self.is_running:
                logger.warning("No active conversation to end")
                return None
            
            # Stop recording and get summary
            summary = self.recording_manager.stop_conversation_recording()
            
            # Get conversation flow summary
            flow_summary = self.conversation_flow.get_conversation_summary()
            
            # Combine summaries
            if summary:
                summary['conversation_flow'] = flow_summary
            
            self.is_running = False
            logger.info("Conversation ended")
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to end conversation: {e}")
            return None
    
    def get_conversation_status(self) -> Dict[str, Any]:
        """Get current conversation status."""
        status = {
            "is_running": self.is_running,
            "recording_status": self.recording_manager.get_recording_status() if self.recording_manager else {},
            "conversation_flow_status": self.conversation_flow.get_conversation_status() if self.conversation_flow else {}
        }
        return status
    
    def _on_recording_start(self, filename: str) -> None:
        """Handle recording start event."""
        logger.info(f"Recording started: {filename}")
    
    def _on_recording_stop(self, filename: str) -> None:
        """Handle recording stop event."""
        logger.info(f"Recording stopped: {filename}")
    
    def _on_transcription(self, transcription: str) -> None:
        """Handle transcription event."""
        logger.debug(f"Transcription: {transcription}")
    
    def _on_conversation_saved(self, summary: Dict[str, Any]) -> None:
        """Handle conversation saved event."""
        logger.info(f"Conversation saved: {summary.get('conversation', {}).get('id', 'unknown')}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def shutdown(self) -> None:
        """Shutdown the application."""
        try:
            if self.is_running:
                self.end_conversation()
            
            if self.recording_manager:
                self.recording_manager.cleanup()
            
            logger.info("Application shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="Stroke Conversation Bot")
    parser.add_argument("--config", default="config/stroke_bot_config.yaml", help="Configuration file path")
    parser.add_argument("--patient-name", help="Patient name for the conversation")
    parser.add_argument("--honorific", default="Mr.", choices=["Mr.", "Ms.", "Dr."], help="Patient honorific")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--server", action="store_true", help="Run in server mode (FastAPI)")
    parser.add_argument("--no-audio", action="store_true", help="Disable audio recording (headless)")
    parser.add_argument("--test", action="store_true", help="Run component tests only")
    
    args = parser.parse_args()
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Initialize bot
    bot = StrokeConversationBot(args.config)
    
    # Propagate no-audio preference via env var to skip audio init
    if args.no_audio:
        import os
        os.environ["STROKE_BOT_NO_AUDIO"] = "1"

    if not bot.initialize():
        logger.error("Failed to initialize bot")
        sys.exit(1)
    
    if args.test:
        logger.info("Component tests completed successfully")
        sys.exit(0)
    
    # If server mode, launch API and exit main loop control to server
    if args.server:
        from server.api import run_server
        run_server()
        return

    # Check if patient name is provided for non-test interactive/CLI mode
    if not args.patient_name:
        logger.error("Patient name is required for conversation mode (non-server)")
        sys.exit(1)
    
    # Start conversation
    if not bot.start_conversation(args.patient_name, args.honorific):
        logger.error("Failed to start conversation")
        sys.exit(1)
    
    if args.interactive:
        # Interactive mode
        print("\n" + "="*60)
        print("🏥 STROKE CONVERSATION BOT")
        print("="*60)
        print("Type 'quit' or 'exit' to end the conversation")
        print("Type 'status' to check conversation status")
        print("="*60 + "\n")
        
        try:
            while bot.is_running:
                user_input = input("👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit']:
                    break
                elif user_input.lower() == 'status':
                    status = bot.get_conversation_status()
                    print(f"\n📊 Status: {status}\n")
                    continue
                elif not user_input:
                    continue
                
                # Process input
                response = bot.process_patient_input(user_input)
                if response:
                    print(f"\n🤖 AI: {response}\n")
                
                # Check if conversation is complete
                if not bot.conversation_flow.state_machine.is_conversation_active():
                    print("\n✅ Conversation completed!")
                    break
        
        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted by user")
        
        finally:
            # End conversation
            summary = bot.end_conversation()
            if summary:
                print(f"\n📋 Conversation Summary:")
                print(f"   Duration: {summary.get('conversation', {}).get('duration_seconds', 0):.1f} seconds")
                print(f"   Responses: {summary.get('response_count', 0)}")
                print(f"   Status: {summary.get('conversation', {}).get('status', 'unknown')}")
    
    else:
        # Non-interactive mode (for API usage)
        logger.info("Bot ready for API usage")
        # Keep running until interrupted
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
    
    bot.shutdown()


if __name__ == "__main__":
    main()
