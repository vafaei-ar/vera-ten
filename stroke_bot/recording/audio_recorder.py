"""
Audio Recorder

Handles real-time audio recording for stroke conversation bot.
"""

import pyaudio
import wave
import threading
import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Real-time audio recorder for conversation recording."""
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 channels: int = 1,
                 chunk_size: int = 1024,
                 format: int = pyaudio.paInt16,
                 output_dir: str = "data/recordings"):
        """Initialize audio recorder."""
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = format
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.recording_thread = None
        self.audio_frames = []
        self.recording_start_time = None
        self.current_filename = None
        
        # Callbacks
        self.on_recording_start: Optional[Callable] = None
        self.on_recording_stop: Optional[Callable] = None
        self.on_audio_chunk: Optional[Callable] = None
        
        # Validate audio device
        self._validate_audio_device()
    
    def _validate_audio_device(self) -> None:
        """Validate that audio device is available."""
        try:
            device_count = self.audio.get_device_count()
            if device_count == 0:
                raise RuntimeError("No audio devices found")
            
            # Check if default input device is available
            default_device = self.audio.get_default_input_device_info()
            logger.info(f"Using audio device: {default_device['name']}")
            
        except Exception as e:
            logger.error(f"Audio device validation failed: {e}")
            raise
    
    def start_recording(self, filename: Optional[str] = None) -> bool:
        """Start audio recording."""
        if self.is_recording:
            logger.warning("Recording already in progress")
            return False
        
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"stroke_conversation_{timestamp}.wav"
            
            self.current_filename = self.output_dir / filename
            
            # Initialize audio stream
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            # Start recording
            self.is_recording = True
            self.audio_frames = []
            self.recording_start_time = datetime.now()
            
            # Start recording thread
            self.recording_thread = threading.Thread(target=self._recording_loop)
            self.recording_thread.start()
            
            # Callback
            if self.on_recording_start:
                self.on_recording_start(str(self.current_filename))
            
            logger.info(f"Started recording: {self.current_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False
    
    def stop_recording(self) -> Optional[str]:
        """Stop audio recording and save file."""
        if not self.is_recording:
            logger.warning("No recording in progress")
            return None
        
        try:
            # Stop recording
            self.is_recording = False
            
            # Wait for recording thread to finish
            if self.recording_thread:
                self.recording_thread.join(timeout=5.0)
            
            # Stop and close stream
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            # Save audio file
            if self.audio_frames and self.current_filename:
                self._save_audio_file()
                
                # Callback
                if self.on_recording_stop:
                    self.on_recording_stop(str(self.current_filename))
                
                logger.info(f"Recording saved: {self.current_filename}")
                return str(self.current_filename)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback for real-time processing."""
        if self.is_recording:
            # Store audio data
            self.audio_frames.append(in_data)
            
            # Callback for real-time processing
            if self.on_audio_chunk:
                try:
                    self.on_audio_chunk(in_data, time_info)
                except Exception as e:
                    logger.warning(f"Audio chunk callback error: {e}")
        
        return (in_data, pyaudio.paContinue)
    
    def _recording_loop(self) -> None:
        """Main recording loop."""
        try:
            while self.is_recording and self.stream:
                # The actual recording happens in the callback
                # This loop just keeps the thread alive
                pass
        except Exception as e:
            logger.error(f"Recording loop error: {e}")
    
    def _save_audio_file(self) -> None:
        """Save recorded audio to file."""
        try:
            with wave.open(str(self.current_filename), 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.audio_frames))
            
            logger.info(f"Audio file saved: {self.current_filename}")
            
        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            raise
    
    def pause_recording(self) -> None:
        """Pause recording (keep stream open but stop storing frames)."""
        if self.is_recording:
            self.is_recording = False
            logger.info("Recording paused")
    
    def resume_recording(self) -> None:
        """Resume recording."""
        if not self.is_recording and self.stream:
            self.is_recording = True
            logger.info("Recording resumed")
    
    def get_recording_duration(self) -> Optional[float]:
        """Get current recording duration in seconds."""
        if self.recording_start_time:
            return (datetime.now() - self.recording_start_time).total_seconds()
        return None
    
    def get_recording_info(self) -> Dict[str, Any]:
        """Get current recording information."""
        return {
            "is_recording": self.is_recording,
            "filename": str(self.current_filename) if self.current_filename else None,
            "duration_seconds": self.get_recording_duration(),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_size": self.chunk_size,
            "frames_recorded": len(self.audio_frames)
        }
    
    def set_audio_chunk_callback(self, callback: Callable) -> None:
        """Set callback for real-time audio chunk processing."""
        self.on_audio_chunk = callback
    
    def set_recording_callbacks(self, 
                               on_start: Optional[Callable] = None,
                               on_stop: Optional[Callable] = None) -> None:
        """Set recording start/stop callbacks."""
        self.on_recording_start = on_start
        self.on_recording_stop = on_stop
    
    def get_audio_level(self) -> float:
        """Get current audio level (0.0 to 1.0)."""
        if not self.audio_frames:
            return 0.0
        
        try:
            # Get the last audio chunk
            last_chunk = self.audio_frames[-1]
            
            # Convert to numpy array
            audio_data = np.frombuffer(last_chunk, dtype=np.int16)
            
            # Calculate RMS level
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Normalize to 0-1 range
            max_rms = 32767.0  # Maximum value for 16-bit audio
            return min(rms / max_rms, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculating audio level: {e}")
            return 0.0
    
    def is_audio_input_active(self, threshold: float = 0.01) -> bool:
        """Check if there's active audio input above threshold."""
        return self.get_audio_level() > threshold
    
    def cleanup(self) -> None:
        """Cleanup audio resources."""
        try:
            if self.is_recording:
                self.stop_recording()
            
            if self.audio:
                self.audio.terminate()
            
            logger.info("Audio recorder cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
