"""
Recording Manager

Orchestrates audio recording, transcription, and storage for stroke conversations.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path
import threading
import time

from .audio_recorder import AudioRecorder
from .transcriber import Transcriber
from .conversation_storage import ConversationStorage

logger = logging.getLogger(__name__)


class RecordingManager:
    """Manages the complete recording workflow for stroke conversations."""
    
    def __init__(self, 
                 storage_dir: str = "data/storage",
                 recording_dir: str = "data/recordings",
                 transcription_dir: str = "data/transcriptions"):
        """Initialize recording manager."""
        self.storage_dir = Path(storage_dir)
        self.recording_dir = Path(recording_dir)
        self.transcription_dir = Path(transcription_dir)
        
        # Create directories
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.recording_dir.mkdir(parents=True, exist_ok=True)
        self.transcription_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.audio_recorder = AudioRecorder(output_dir=str(self.recording_dir))
        self.transcriber = Transcriber()
        self.storage = ConversationStorage(
            db_path=str(self.storage_dir / "conversations.db"),
            storage_dir=str(self.storage_dir)
        )
        
        # State
        self.current_conversation_id = None
        self.is_recording = False
        self.recording_thread = None
        
        # Callbacks
        self.on_recording_start: Optional[Callable] = None
        self.on_recording_stop: Optional[Callable] = None
        self.on_transcription: Optional[Callable] = None
        self.on_conversation_saved: Optional[Callable] = None
        
        # Setup audio recorder callbacks
        self.audio_recorder.set_recording_callbacks(
            on_start=self._on_recording_start,
            on_stop=self._on_recording_stop
        )
        self.audio_recorder.set_audio_chunk_callback(self._on_audio_chunk)
        
        # Setup transcriber callbacks
        self.transcriber.set_transcription_callback(self._on_transcription)
        self.transcriber.set_error_callback(self._on_transcription_error)
        
        logger.info("Recording manager initialized")
    
    def start_conversation_recording(self, 
                                   patient_name: str,
                                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start recording a new conversation."""
        try:
            # Create conversation record
            self.current_conversation_id = self.storage.create_conversation(
                patient_name=patient_name,
                metadata=metadata
            )
            
            # Start audio recording
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"conversation_{self.current_conversation_id}_{timestamp}.wav"
            
            success = self.audio_recorder.start_recording(audio_filename)
            if not success:
                logger.error("Failed to start audio recording")
                return None
            
            self.is_recording = True
            
            # Start real-time transcription thread
            self.recording_thread = threading.Thread(target=self._recording_loop)
            self.recording_thread.start()
            
            logger.info(f"Started conversation recording: {self.current_conversation_id}")
            return self.current_conversation_id
            
        except Exception as e:
            logger.error(f"Failed to start conversation recording: {e}")
            return None
    
    def stop_conversation_recording(self) -> Optional[Dict[str, Any]]:
        """Stop recording and save conversation data."""
        try:
            if not self.is_recording or not self.current_conversation_id:
                logger.warning("No active recording to stop")
                return None
            
            # Stop audio recording
            audio_file_path = self.audio_recorder.stop_recording()
            if not audio_file_path:
                logger.error("Failed to stop audio recording")
                return None
            
            self.is_recording = False
            
            # Wait for recording thread to finish
            if self.recording_thread:
                self.recording_thread.join(timeout=5.0)
            
            # Transcribe the complete audio file
            transcription = self.transcriber.transcribe_file(audio_file_path)
            
            # Save transcription to file
            transcription_file_path = None
            if transcription:
                transcription_file_path = self._save_transcription(transcription)
            
            # Update conversation record
            end_time = datetime.now()
            duration = self.audio_recorder.get_recording_duration()
            
            self.storage.update_conversation(
                conversation_id=self.current_conversation_id,
                end_time=end_time,
                status="completed",
                audio_file_path=audio_file_path,
                transcription_file_path=transcription_file_path,
                metadata={"duration_seconds": duration}
            )
            
            # Get conversation summary
            summary = self.storage.get_conversation_summary(self.current_conversation_id)
            
            # Callback
            if self.on_conversation_saved:
                self.on_conversation_saved(summary)
            
            logger.info(f"Conversation recording completed: {self.current_conversation_id}")
            
            # Reset state
            conversation_id = self.current_conversation_id
            self.current_conversation_id = None
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to stop conversation recording: {e}")
            return None
    
    def add_conversation_response(self, 
                                question_key: str,
                                question_text: str,
                                response_text: str,
                                section: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a response to the current conversation."""
        if not self.current_conversation_id:
            logger.warning("No active conversation to add response to")
            return False
        
        try:
            success = self.storage.add_response(
                conversation_id=self.current_conversation_id,
                question_key=question_key,
                question_text=question_text,
                response_text=response_text,
                section=section,
                metadata=metadata
            )
            
            if success:
                logger.debug(f"Added response for question: {question_key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add conversation response: {e}")
            return False
    
    def get_current_conversation_id(self) -> Optional[str]:
        """Get the current conversation ID."""
        return self.current_conversation_id
    
    def is_conversation_active(self) -> bool:
        """Check if a conversation is currently being recorded."""
        return self.is_recording and self.current_conversation_id is not None
    
    def get_recording_status(self) -> Dict[str, Any]:
        """Get current recording status."""
        return {
            "is_recording": self.is_recording,
            "conversation_id": self.current_conversation_id,
            "recording_duration": self.audio_recorder.get_recording_duration(),
            "audio_level": self.audio_recorder.get_audio_level(),
            "is_audio_active": self.audio_recorder.is_audio_input_active()
        }
    
    def _recording_loop(self) -> None:
        """Main recording loop for real-time processing."""
        try:
            while self.is_recording:
                # This loop handles real-time audio processing
                # The actual recording happens in the audio recorder callback
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Recording loop error: {e}")
    
    def _on_recording_start(self, filename: str) -> None:
        """Handle recording start event."""
        logger.info(f"Recording started: {filename}")
        if self.on_recording_start:
            self.on_recording_start(filename)
    
    def _on_recording_stop(self, filename: str) -> None:
        """Handle recording stop event."""
        logger.info(f"Recording stopped: {filename}")
        if self.on_recording_stop:
            self.on_recording_stop(filename)
    
    def _on_audio_chunk(self, audio_chunk: bytes, time_info: Dict[str, Any]) -> None:
        """Handle real-time audio chunk."""
        try:
            # Transcribe audio chunk in real-time
            transcription = self.transcriber.transcribe_realtime_chunk(audio_chunk)
            
            if transcription:
                logger.debug(f"Real-time transcription: {transcription}")
                
        except Exception as e:
            logger.warning(f"Error processing audio chunk: {e}")
    
    def _on_transcription(self, transcription: str) -> None:
        """Handle transcription result."""
        logger.debug(f"Transcription: {transcription}")
        if self.on_transcription:
            self.on_transcription(transcription)
    
    def _on_transcription_error(self, error: str) -> None:
        """Handle transcription error."""
        logger.warning(f"Transcription error: {error}")
    
    def _save_transcription(self, transcription: str) -> str:
        """Save transcription to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcription_{self.current_conversation_id}_{timestamp}.txt"
            filepath = self.transcription_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(transcription)
            
            logger.info(f"Transcription saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save transcription: {e}")
            return None
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        return self.storage.get_conversation(conversation_id)
    
    def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation summary by ID."""
        return self.storage.get_conversation_summary(conversation_id)
    
    def get_conversations_by_patient(self, patient_name: str) -> List[Dict[str, Any]]:
        """Get all conversations for a patient."""
        return self.storage.get_conversations_by_patient(patient_name)
    
    def export_conversation(self, conversation_id: str, format: str = "json") -> Optional[str]:
        """Export conversation data."""
        return self.storage.export_conversation(conversation_id, format)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and associated files."""
        return self.storage.delete_conversation(conversation_id)
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return self.storage.get_storage_stats()
    
    def set_callbacks(self,
                     on_recording_start: Optional[Callable] = None,
                     on_recording_stop: Optional[Callable] = None,
                     on_transcription: Optional[Callable] = None,
                     on_conversation_saved: Optional[Callable] = None) -> None:
        """Set recording manager callbacks."""
        self.on_recording_start = on_recording_start
        self.on_recording_stop = on_recording_stop
        self.on_transcription = on_transcription
        self.on_conversation_saved = on_conversation_saved
    
    def cleanup(self) -> None:
        """Cleanup recording manager resources."""
        try:
            if self.is_recording:
                self.stop_conversation_recording()
            
            self.audio_recorder.cleanup()
            logger.info("Recording manager cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
