"""
Conversation Storage

Handles storage and retrieval of conversation data, including audio files,
transcriptions, and structured conversation data.
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import uuid
import shutil

logger = logging.getLogger(__name__)


class ConversationStorage:
    """Manages storage and retrieval of conversation data."""
    
    def __init__(self, db_path: str = "data/conversations.db", 
                 storage_dir: str = "data/storage"):
        """Initialize conversation storage."""
        self.db_path = Path(db_path)
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create database and tables
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Conversations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        patient_name TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        duration_seconds REAL,
                        status TEXT NOT NULL,
                        emergency_detected BOOLEAN DEFAULT FALSE,
                        audio_file_path TEXT,
                        transcription_file_path TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Responses table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS responses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT NOT NULL,
                        question_key TEXT NOT NULL,
                        question_text TEXT NOT NULL,
                        response_text TEXT NOT NULL,
                        response_timestamp TEXT NOT NULL,
                        section TEXT,
                        metadata TEXT,
                        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                    )
                """)
                
                # Audio segments table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audio_segments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT NOT NULL,
                        segment_number INTEGER NOT NULL,
                        start_time REAL NOT NULL,
                        end_time REAL NOT NULL,
                        audio_file_path TEXT NOT NULL,
                        transcription TEXT,
                        confidence REAL,
                        metadata TEXT,
                        FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_patient ON conversations (patient_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_start_time ON conversations (start_time)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_conversation ON responses (conversation_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_question ON responses (question_key)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_audio_segments_conversation ON audio_segments (conversation_id)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_conversation(self, 
                          patient_name: str,
                          start_time: Optional[datetime] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new conversation record."""
        conversation_id = str(uuid.uuid4())
        start_time = start_time or datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO conversations 
                    (id, patient_name, start_time, status, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    conversation_id,
                    patient_name,
                    start_time.isoformat(),
                    "active",
                    json.dumps(metadata or {})
                ))
                conn.commit()
                
                logger.info(f"Created conversation: {conversation_id}")
                return conversation_id
                
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    def update_conversation(self, 
                          conversation_id: str,
                          end_time: Optional[datetime] = None,
                          status: Optional[str] = None,
                          emergency_detected: Optional[bool] = None,
                          audio_file_path: Optional[str] = None,
                          transcription_file_path: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update conversation record."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build update query dynamically
                updates = []
                params = []
                
                if end_time:
                    updates.append("end_time = ?")
                    params.append(end_time.isoformat())
                
                if status:
                    updates.append("status = ?")
                    params.append(status)
                
                if emergency_detected is not None:
                    updates.append("emergency_detected = ?")
                    params.append(emergency_detected)
                
                if audio_file_path:
                    updates.append("audio_file_path = ?")
                    params.append(audio_file_path)
                
                if transcription_file_path:
                    updates.append("transcription_file_path = ?")
                    params.append(transcription_file_path)
                
                if metadata:
                    updates.append("metadata = ?")
                    params.append(json.dumps(metadata))
                
                if updates:
                    params.append(conversation_id)
                    query = f"UPDATE conversations SET {', '.join(updates)} WHERE id = ?"
                    cursor.execute(query, params)
                    conn.commit()
                    
                    logger.info(f"Updated conversation: {conversation_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to update conversation: {e}")
            return False
    
    def add_response(self, 
                    conversation_id: str,
                    question_key: str,
                    question_text: str,
                    response_text: str,
                    response_timestamp: Optional[datetime] = None,
                    section: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a patient response to the conversation."""
        response_timestamp = response_timestamp or datetime.now()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO responses 
                    (conversation_id, question_key, question_text, response_text, 
                     response_timestamp, section, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    conversation_id,
                    question_key,
                    question_text,
                    response_text,
                    response_timestamp.isoformat(),
                    section,
                    json.dumps(metadata or {})
                ))
                conn.commit()
                
                logger.debug(f"Added response for question {question_key}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add response: {e}")
            return False
    
    def add_audio_segment(self, 
                         conversation_id: str,
                         segment_number: int,
                         start_time: float,
                         end_time: float,
                         audio_file_path: str,
                         transcription: Optional[str] = None,
                         confidence: Optional[float] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add an audio segment to the conversation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audio_segments 
                    (conversation_id, segment_number, start_time, end_time, 
                     audio_file_path, transcription, confidence, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conversation_id,
                    segment_number,
                    start_time,
                    end_time,
                    audio_file_path,
                    transcription,
                    confidence,
                    json.dumps(metadata or {})
                ))
                conn.commit()
                
                logger.debug(f"Added audio segment {segment_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to add audio segment: {e}")
            return False
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return None
    
    def get_conversation_responses(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all responses for a conversation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM responses 
                    WHERE conversation_id = ? 
                    ORDER BY response_timestamp
                """, (conversation_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get conversation responses: {e}")
            return []
    
    def get_conversation_audio_segments(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all audio segments for a conversation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM audio_segments 
                    WHERE conversation_id = ? 
                    ORDER BY segment_number
                """, (conversation_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get audio segments: {e}")
            return []
    
    def get_conversations_by_patient(self, patient_name: str) -> List[Dict[str, Any]]:
        """Get all conversations for a patient."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM conversations 
                    WHERE patient_name = ? 
                    ORDER BY start_time DESC
                """, (patient_name,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get conversations by patient: {e}")
            return []
    
    def get_conversations_by_date_range(self, 
                                      start_date: datetime, 
                                      end_date: datetime) -> List[Dict[str, Any]]:
        """Get conversations within a date range."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM conversations 
                    WHERE start_time >= ? AND start_time <= ? 
                    ORDER BY start_time DESC
                """, (start_date.isoformat(), end_date.isoformat()))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get conversations by date range: {e}")
            return []
    
    def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a complete summary of a conversation."""
        try:
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                return None
            
            responses = self.get_conversation_responses(conversation_id)
            audio_segments = self.get_conversation_audio_segments(conversation_id)
            
            return {
                "conversation": conversation,
                "responses": responses,
                "audio_segments": audio_segments,
                "response_count": len(responses),
                "audio_segment_count": len(audio_segments),
                "total_duration": conversation.get("duration_seconds", 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            return None
    
    def export_conversation(self, conversation_id: str, format: str = "json") -> Optional[str]:
        """Export conversation data in specified format."""
        try:
            summary = self.get_conversation_summary(conversation_id)
            if not summary:
                return None
            
            if format.lower() == "json":
                return json.dumps(summary, indent=2, default=str)
            elif format.lower() == "csv":
                return self._export_to_csv(summary)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export conversation: {e}")
            return None
    
    def _export_to_csv(self, summary: Dict[str, Any]) -> str:
        """Export conversation to CSV format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write conversation info
        conversation = summary["conversation"]
        writer.writerow(["Conversation ID", conversation["id"]])
        writer.writerow(["Patient Name", conversation["patient_name"]])
        writer.writerow(["Start Time", conversation["start_time"]])
        writer.writerow(["End Time", conversation.get("end_time", "N/A")])
        writer.writerow(["Duration", conversation.get("duration_seconds", 0)])
        writer.writerow(["Status", conversation["status"]])
        writer.writerow([])
        
        # Write responses
        writer.writerow(["Question Key", "Question Text", "Response Text", "Timestamp", "Section"])
        for response in summary["responses"]:
            writer.writerow([
                response["question_key"],
                response["question_text"],
                response["response_text"],
                response["response_timestamp"],
                response.get("section", "")
            ])
        
        return output.getvalue()
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all associated data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get conversation info for file cleanup
                conversation = self.get_conversation(conversation_id)
                if conversation:
                    # Delete associated files
                    if conversation.get("audio_file_path"):
                        audio_path = Path(conversation["audio_file_path"])
                        if audio_path.exists():
                            audio_path.unlink()
                    
                    if conversation.get("transcription_file_path"):
                        trans_path = Path(conversation["transcription_file_path"])
                        if trans_path.exists():
                            trans_path.unlink()
                
                # Delete from database
                cursor.execute("DELETE FROM audio_segments WHERE conversation_id = ?", (conversation_id,))
                cursor.execute("DELETE FROM responses WHERE conversation_id = ?", (conversation_id,))
                cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
                
                conn.commit()
                logger.info(f"Deleted conversation: {conversation_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get conversation count
                cursor.execute("SELECT COUNT(*) FROM conversations")
                conversation_count = cursor.fetchone()[0]
                
                # Get response count
                cursor.execute("SELECT COUNT(*) FROM responses")
                response_count = cursor.fetchone()[0]
                
                # Get audio segment count
                cursor.execute("SELECT COUNT(*) FROM audio_segments")
                audio_segment_count = cursor.fetchone()[0]
                
                # Get storage directory size
                storage_size = sum(f.stat().st_size for f in self.storage_dir.rglob('*') if f.is_file())
                
                return {
                    "conversation_count": conversation_count,
                    "response_count": response_count,
                    "audio_segment_count": audio_segment_count,
                    "storage_size_bytes": storage_size,
                    "storage_size_mb": storage_size / (1024 * 1024),
                    "database_path": str(self.db_path),
                    "storage_directory": str(self.storage_dir)
                }
                
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}
