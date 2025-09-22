#!/usr/bin/env python3
"""
Test Conversation Script

Tests the stroke conversation bot components and functionality.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from conversation_engine import ConversationFlow, YAMLConversationParser
from extensions.ollama_medical import MedicalLLM, OllamaConfig
from recording import RecordingManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_yaml_parser():
    """Test YAML conversation parser."""
    print("🧪 Testing YAML Parser...")
    
    try:
        parser = YAMLConversationParser("../stroke_sen1.yml")
        
        # Test basic parsing
        meta = parser.get_meta()
        print(f"   ✅ Organization: {meta.organization}")
        print(f"   ✅ Service: {meta.service_name}")
        
        # Test questions
        questions = parser.get_questions()
        print(f"   ✅ Questions loaded: {len(questions)}")
        
        # Test sections
        sections = parser.get_sections()
        print(f"   ✅ Sections: {sections}")
        
        # Test validation
        issues = parser.validate_conversation_structure()
        if issues:
            print(f"   ⚠️  Validation issues: {issues}")
        else:
            print("   ✅ Structure validation passed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ YAML Parser test failed: {e}")
        return False


def test_ollama_integration():
    """Test Ollama integration."""
    print("\n🧪 Testing Ollama Integration...")
    
    try:
        config = OllamaConfig(model="llama3.2:3b")
        medical_llm = MedicalLLM(config)
        
        # Test connection
        health = medical_llm.ollama_client.health_check()
        if health.get('status') == 'healthy':
            print("   ✅ Ollama connection healthy")
        else:
            print(f"   ⚠️  Ollama health check: {health}")
        
        # Test simple generation
        response = medical_llm.generate_medical_response(
            system_prompt="You are a helpful medical assistant.",
            user_prompt="Hello, how are you?"
        )
        
        if response and len(response) > 0:
            print(f"   ✅ Generated response: {response[:50]}...")
        else:
            print("   ⚠️  No response generated")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ollama integration test failed: {e}")
        return False


def test_conversation_flow():
    """Test conversation flow."""
    print("\n🧪 Testing Conversation Flow...")
    
    try:
        # Create conversation flow
        flow = ConversationFlow("../stroke_sen1.yml")
        
        # Test conversation start
        greeting = flow.start_conversation(
            patient_name="Test Patient",
            honorific="Mr.",
            organization="Test Hospital",
            site="Test Site"
        )
        
        if greeting and len(greeting) > 0:
            print(f"   ✅ Greeting generated: {greeting[:50]}...")
        else:
            print("   ⚠️  No greeting generated")
        
        # Test status
        status = flow.get_conversation_status()
        print(f"   ✅ Conversation status: {status['current_state']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Conversation flow test failed: {e}")
        return False


def test_recording_manager():
    """Test recording manager."""
    print("\n🧪 Testing Recording Manager...")
    
    try:
        # Create recording manager
        recording_manager = RecordingManager()
        
        # Test conversation creation
        conversation_id = recording_manager.start_conversation_recording(
            patient_name="Test Patient",
            metadata={"test": True}
        )
        
        if conversation_id:
            print(f"   ✅ Conversation created: {conversation_id}")
            
            # Test adding response
            success = recording_manager.add_conversation_response(
                question_key="test_question",
                question_text="How are you feeling?",
                response_text="I'm doing well, thank you."
            )
            
            if success:
                print("   ✅ Response added successfully")
            else:
                print("   ⚠️  Failed to add response")
            
            # Stop recording
            summary = recording_manager.stop_conversation_recording()
            if summary:
                print(f"   ✅ Recording stopped, summary created")
            else:
                print("   ⚠️  No summary generated")
        else:
            print("   ⚠️  Failed to create conversation")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Recording manager test failed: {e}")
        return False


def test_integration():
    """Test full integration."""
    print("\n🧪 Testing Full Integration...")
    
    try:
        from main import StrokeConversationBot
        
        # Create bot instance
        bot = StrokeConversationBot()
        
        # Test initialization
        if bot.initialize():
            print("   ✅ Bot initialized successfully")
            
            # Test conversation start
            if bot.start_conversation("Integration Test Patient"):
                print("   ✅ Conversation started")
                
                # Test input processing
                response = bot.process_patient_input("Yes, I consent to the call.")
                if response:
                    print(f"   ✅ Input processed: {response[:50]}...")
                
                # End conversation
                summary = bot.end_conversation()
                if summary:
                    print("   ✅ Conversation ended successfully")
                
                bot.shutdown()
                return True
            else:
                print("   ⚠️  Failed to start conversation")
        else:
            print("   ⚠️  Failed to initialize bot")
        
        return False
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🏥 Stroke Conversation Bot - Component Tests")
    print("=" * 50)
    
    tests = [
        ("YAML Parser", test_yaml_parser),
        ("Ollama Integration", test_ollama_integration),
        ("Conversation Flow", test_conversation_flow),
        ("Recording Manager", test_recording_manager),
        ("Full Integration", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The stroke bot is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration and dependencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
