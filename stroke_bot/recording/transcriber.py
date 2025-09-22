"""
Transcriber

Handles speech-to-text transcription for recorded audio and real-time transcription.
"""

import speech_recognition as sr
import logging
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
import wave
import tempfile
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class Transcriber:
    """Speech-to-text transcriber for audio files and real-time audio."""
    
    def __init__(self, 
                 language: str = "en-US",
                 use_google: bool = True,
                 use_offline: bool = True):
        """Initialize transcriber with speech recognition options."""
        self.language = language
        self.use_google = use_google
        self.use_offline = use_offline
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.8
        
        # Callbacks
        self.on_transcription: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        logger.info(f"Transcriber initialized - Language: {language}, Google: {use_google}, Offline: {use_offline}")
    
    def transcribe_file(self, audio_file_path: str) -> Optional[str]:
        """Transcribe an audio file to text."""
        try:
            audio_file = Path(audio_file_path)
            if not audio_file.exists():
                logger.error(f"Audio file not found: {audio_file_path}")
                return None
            
            # Load audio file
            with sr.AudioFile(str(audio_file)) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.record(source)
            
            # Transcribe using available methods
            transcription = self._transcribe_audio(audio)
            
            if transcription:
                logger.info(f"Transcription completed for {audio_file_path}")
                return transcription
            else:
                logger.warning(f"No transcription result for {audio_file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error transcribing file {audio_file_path}: {e}")
            if self.on_error:
                self.on_error(str(e))
            return None
    
    def transcribe_audio_data(self, audio_data: bytes, sample_rate: int = 16000) -> Optional[str]:
        """Transcribe raw audio data."""
        try:
            # Create temporary file for audio data
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # Write audio data to temporary file
                self._write_audio_data_to_wav(temp_file.name, audio_data, sample_rate)
                
                # Transcribe the temporary file
                transcription = self.transcribe_file(temp_file.name)
                
                # Clean up temporary file
                os.unlink(temp_file.name)
                
                return transcription
                
        except Exception as e:
            logger.error(f"Error transcribing audio data: {e}")
            return None
    
    def transcribe_realtime_chunk(self, audio_chunk: bytes, sample_rate: int = 16000) -> Optional[str]:
        """Transcribe a real-time audio chunk."""
        try:
            # Convert audio chunk to AudioData
            audio_data = sr.AudioData(audio_chunk, sample_rate, 2)  # 2 bytes per sample
            
            # Transcribe
            transcription = self._transcribe_audio(audio_data)
            
            if transcription and self.on_transcription:
                self.on_transcription(transcription)
            
            return transcription
            
        except Exception as e:
            logger.warning(f"Error transcribing real-time chunk: {e}")
            return None
    
    def _transcribe_audio(self, audio: sr.AudioData) -> Optional[str]:
        """Transcribe audio data using available recognition methods."""
        transcription = None
        
        # Try Google Speech Recognition first (if enabled)
        if self.use_google:
            try:
                transcription = self.recognizer.recognize_google(audio, language=self.language)
                logger.debug("Transcription using Google Speech Recognition")
                return transcription
            except sr.UnknownValueError:
                logger.debug("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                logger.warning(f"Google Speech Recognition error: {e}")
        
        # Try offline recognition (if enabled)
        if self.use_offline and not transcription:
            try:
                # Try Sphinx (offline)
                transcription = self.recognizer.recognize_sphinx(audio)
                logger.debug("Transcription using Sphinx (offline)")
                return transcription
            except sr.UnknownValueError:
                logger.debug("Sphinx could not understand audio")
            except sr.RequestError as e:
                logger.warning(f"Sphinx error: {e}")
        
        return transcription
    
    def _write_audio_data_to_wav(self, filename: str, audio_data: bytes, sample_rate: int) -> None:
        """Write raw audio data to WAV file."""
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)
    
    def transcribe_conversation_segments(self, audio_file_path: str, segment_duration: int = 30) -> List[Dict[str, Any]]:
        """Transcribe audio file in segments for better accuracy."""
        try:
            audio_file = Path(audio_file_path)
            if not audio_file.exists():
                logger.error(f"Audio file not found: {audio_file_path}")
                return []
            
            segments = []
            
            with sr.AudioFile(str(audio_file)) as source:
                # Get total duration
                duration = source.DURATION
                total_segments = int(duration / segment_duration) + 1
                
                for i in range(total_segments):
                    start_time = i * segment_duration
                    end_time = min((i + 1) * segment_duration, duration)
                    
                    # Record segment
                    source.seek(start_time)
                    audio = self.recognizer.record(source, duration=end_time - start_time)
                    
                    # Transcribe segment
                    transcription = self._transcribe_audio(audio)
                    
                    if transcription:
                        segments.append({
                            'segment': i + 1,
                            'start_time': start_time,
                            'end_time': end_time,
                            'transcription': transcription,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        logger.debug(f"Transcribed segment {i + 1}/{total_segments}")
            
            logger.info(f"Transcribed {len(segments)} segments from {audio_file_path}")
            return segments
            
        except Exception as e:
            logger.error(f"Error transcribing conversation segments: {e}")
            return []
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return [
            "en-US", "en-GB", "en-AU", "en-CA",
            "es-ES", "es-MX", "fr-FR", "de-DE",
            "it-IT", "pt-BR", "ru-RU", "ja-JP",
            "ko-KR", "zh-CN", "zh-TW"
        ]
    
    def set_language(self, language: str) -> bool:
        """Set transcription language."""
        if language in self.get_supported_languages():
            self.language = language
            logger.info(f"Transcription language set to: {language}")
            return True
        else:
            logger.warning(f"Unsupported language: {language}")
            return False
    
    def set_transcription_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for real-time transcription results."""
        self.on_transcription = callback
    
    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for transcription errors."""
        self.on_error = callback
    
    def adjust_for_ambient_noise(self, duration: float = 1.0) -> None:
        """Adjust recognizer for ambient noise."""
        try:
            with sr.Microphone() as source:
                logger.info(f"Adjusting for ambient noise for {duration} seconds...")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                logger.info("Ambient noise adjustment complete")
        except Exception as e:
            logger.warning(f"Could not adjust for ambient noise: {e}")
    
    def get_recognition_config(self) -> Dict[str, Any]:
        """Get current recognition configuration."""
        return {
            "language": self.language,
            "energy_threshold": self.recognizer.energy_threshold,
            "dynamic_energy_threshold": self.recognizer.dynamic_energy_threshold,
            "pause_threshold": self.recognizer.pause_threshold,
            "phrase_threshold": self.recognizer.phrase_threshold,
            "non_speaking_duration": self.recognizer.non_speaking_duration,
            "use_google": self.use_google,
            "use_offline": self.use_offline
        }
    
    def test_recognition(self) -> bool:
        """Test speech recognition with microphone."""
        try:
            with sr.Microphone() as source:
                logger.info("Testing speech recognition...")
                audio = self.recognizer.listen(source, timeout=5)
                transcription = self._transcribe_audio(audio)
                
                if transcription:
                    logger.info(f"Test successful: '{transcription}'")
                    return True
                else:
                    logger.warning("Test failed: No transcription result")
                    return False
                    
        except Exception as e:
            logger.error(f"Recognition test failed: {e}")
            return False
