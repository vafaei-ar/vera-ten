#!/usr/bin/env python3
"""
Export Data Script

Exports conversation data in various formats for analysis and reporting.
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
import json
import csv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from recording import ConversationStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def export_conversation(conversation_id: str, output_format: str = "json", output_file: str = None):
    """Export a specific conversation."""
    try:
        storage = ConversationStorage()
        
        # Get conversation summary
        summary = storage.get_conversation_summary(conversation_id)
        if not summary:
            print(f"❌ Conversation {conversation_id} not found")
            return False
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"conversation_{conversation_id}_{timestamp}.{output_format}"
        
        # Export data
        if output_format.lower() == "json":
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, default=str)
        
        elif output_format.lower() == "csv":
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # Write conversation info
                conv = summary['conversation']
                writer.writerow(['Field', 'Value'])
                writer.writerow(['Conversation ID', conv['id']])
                writer.writerow(['Patient Name', conv['patient_name']])
                writer.writerow(['Start Time', conv['start_time']])
                writer.writerow(['End Time', conv.get('end_time', 'N/A')])
                writer.writerow(['Duration (seconds)', conv.get('duration_seconds', 0)])
                writer.writerow(['Status', conv['status']])
                writer.writerow(['Emergency Detected', conv.get('emergency_detected', False)])
                writer.writerow([])
                
                # Write responses
                writer.writerow(['Question Key', 'Question Text', 'Response Text', 'Timestamp', 'Section'])
                for response in summary['responses']:
                    writer.writerow([
                        response['question_key'],
                        response['question_text'],
                        response['response_text'],
                        response['response_timestamp'],
                        response.get('section', '')
                    ])
        
        else:
            print(f"❌ Unsupported format: {output_format}")
            return False
        
        print(f"✅ Conversation exported to {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False


def export_patient_data(patient_name: str, output_format: str = "json", output_file: str = None):
    """Export all conversations for a patient."""
    try:
        storage = ConversationStorage()
        
        # Get all conversations for patient
        conversations = storage.get_conversations_by_patient(patient_name)
        if not conversations:
            print(f"❌ No conversations found for patient: {patient_name}")
            return False
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = patient_name.replace(" ", "_").replace("/", "_")
            output_file = f"patient_{safe_name}_{timestamp}.{output_format}"
        
        # Export data
        if output_format.lower() == "json":
            data = {
                "patient_name": patient_name,
                "conversation_count": len(conversations),
                "conversations": conversations,
                "export_timestamp": datetime.now().isoformat()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        
        elif output_format.lower() == "csv":
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # Write patient summary
                writer.writerow(['Patient Name', patient_name])
                writer.writerow(['Total Conversations', len(conversations)])
                writer.writerow(['Export Date', datetime.now().isoformat()])
                writer.writerow([])
                
                # Write conversation headers
                writer.writerow(['Conversation ID', 'Start Time', 'End Time', 'Duration', 'Status', 'Emergency'])
                
                # Write conversation data
                for conv in conversations:
                    writer.writerow([
                        conv['id'],
                        conv['start_time'],
                        conv.get('end_time', 'N/A'),
                        conv.get('duration_seconds', 0),
                        conv['status'],
                        conv.get('emergency_detected', False)
                    ])
        
        else:
            print(f"❌ Unsupported format: {output_format}")
            return False
        
        print(f"✅ Patient data exported to {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False


def export_date_range(start_date: str, end_date: str, output_format: str = "json", output_file: str = None):
    """Export conversations within a date range."""
    try:
        storage = ConversationStorage()
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Get conversations in date range
        conversations = storage.get_conversations_by_date_range(start_dt, end_dt)
        if not conversations:
            print(f"❌ No conversations found in date range: {start_date} to {end_date}")
            return False
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            start_str = start_dt.strftime("%Y%m%d")
            end_str = end_dt.strftime("%Y%m%d")
            output_file = f"conversations_{start_str}_{end_str}_{timestamp}.{output_format}"
        
        # Export data
        if output_format.lower() == "json":
            data = {
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "conversation_count": len(conversations),
                "conversations": conversations,
                "export_timestamp": datetime.now().isoformat()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        
        elif output_format.lower() == "csv":
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # Write date range info
                writer.writerow(['Date Range', f"{start_date} to {end_date}"])
                writer.writerow(['Total Conversations', len(conversations)])
                writer.writerow(['Export Date', datetime.now().isoformat()])
                writer.writerow([])
                
                # Write conversation headers
                writer.writerow(['Conversation ID', 'Patient Name', 'Start Time', 'End Time', 'Duration', 'Status', 'Emergency'])
                
                # Write conversation data
                for conv in conversations:
                    writer.writerow([
                        conv['id'],
                        conv['patient_name'],
                        conv['start_time'],
                        conv.get('end_time', 'N/A'),
                        conv.get('duration_seconds', 0),
                        conv['status'],
                        conv.get('emergency_detected', False)
                    ])
        
        else:
            print(f"❌ Unsupported format: {output_format}")
            return False
        
        print(f"✅ Date range data exported to {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False


def list_conversations(limit: int = 10):
    """List recent conversations."""
    try:
        storage = ConversationStorage()
        
        # Get recent conversations (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        conversations = storage.get_conversations_by_date_range(start_date, end_date)
        
        if not conversations:
            print("❌ No conversations found")
            return False
        
        # Sort by start time (most recent first)
        conversations.sort(key=lambda x: x['start_time'], reverse=True)
        
        # Limit results
        conversations = conversations[:limit]
        
        print(f"📋 Recent Conversations (last {limit}):")
        print("-" * 80)
        print(f"{'ID':<36} {'Patient':<20} {'Start Time':<20} {'Duration':<10} {'Status':<10}")
        print("-" * 80)
        
        for conv in conversations:
            duration = conv.get('duration_seconds', 0)
            duration_str = f"{duration:.1f}s" if duration else "N/A"
            
            start_time = conv['start_time'][:19] if conv['start_time'] else "N/A"
            
            print(f"{conv['id']:<36} {conv['patient_name']:<20} {start_time:<20} {duration_str:<10} {conv['status']:<10}")
        
        return True
        
    except Exception as e:
        print(f"❌ List failed: {e}")
        return False


def get_storage_stats():
    """Get storage statistics."""
    try:
        storage = ConversationStorage()
        stats = storage.get_storage_stats()
        
        print("📊 Storage Statistics:")
        print("-" * 40)
        print(f"Total Conversations: {stats.get('conversation_count', 0)}")
        print(f"Total Responses: {stats.get('response_count', 0)}")
        print(f"Total Audio Segments: {stats.get('audio_segment_count', 0)}")
        print(f"Storage Size: {stats.get('storage_size_mb', 0):.2f} MB")
        print(f"Database Path: {stats.get('database_path', 'N/A')}")
        print(f"Storage Directory: {stats.get('storage_directory', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Stats failed: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Export conversation data")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Export conversation command
    conv_parser = subparsers.add_parser('conversation', help='Export specific conversation')
    conv_parser.add_argument('conversation_id', help='Conversation ID to export')
    conv_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    conv_parser.add_argument('--output', help='Output file path')
    
    # Export patient command
    patient_parser = subparsers.add_parser('patient', help='Export patient data')
    patient_parser.add_argument('patient_name', help='Patient name to export')
    patient_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    patient_parser.add_argument('--output', help='Output file path')
    
    # Export date range command
    date_parser = subparsers.add_parser('date-range', help='Export conversations by date range')
    date_parser.add_argument('start_date', help='Start date (YYYY-MM-DD)')
    date_parser.add_argument('end_date', help='End date (YYYY-MM-DD)')
    date_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    date_parser.add_argument('--output', help='Output file path')
    
    # List conversations command
    list_parser = subparsers.add_parser('list', help='List recent conversations')
    list_parser.add_argument('--limit', type=int, default=10, help='Number of conversations to show')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show storage statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create output directory
    Path("exports").mkdir(exist_ok=True)
    
    if args.command == 'conversation':
        return 0 if export_conversation(args.conversation_id, args.format, args.output) else 1
    
    elif args.command == 'patient':
        return 0 if export_patient_data(args.patient_name, args.format, args.output) else 1
    
    elif args.command == 'date-range':
        return 0 if export_date_range(args.start_date, args.end_date, args.format, args.output) else 1
    
    elif args.command == 'list':
        return 0 if list_conversations(args.limit) else 1
    
    elif args.command == 'stats':
        return 0 if get_storage_stats() else 1
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
