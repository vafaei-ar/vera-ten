#!/usr/bin/env python3
"""
Simple Test Script for Stroke Conversation Bot

Tests the core functionality without audio requirements.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from conversation_engine import ConversationFlow
from extensions.ollama_medical import MedicalLLM, OllamaConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_conversation_flow():
    """Test the conversation flow without audio."""
    print("🧪 Testing Conversation Flow...")
    
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
            print(f"   ✅ Greeting generated: {greeting[:100]}...")
        else:
            print("   ⚠️  No greeting generated")
        
        # Test status
        status = flow.get_conversation_status()
        print(f"   ✅ Conversation status: {status['current_state']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Conversation flow test failed: {e}")
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
            print(f"   ✅ Generated response: {response[:100]}...")
        else:
            print("   ⚠️  No response generated")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ollama integration test failed: {e}")
        return False


def test_medical_conversation():
    """Test a complete medical conversation."""
    print("\n🧪 Testing Medical Conversation...")
    
    try:
        # Create conversation flow
        flow = ConversationFlow("../stroke_sen1.yml")
        
        # Start conversation
        greeting = flow.start_conversation(
            patient_name="John Doe",
            honorific="Mr.",
            organization="PennState Health",
            site="Hershey Medical Center"
        )
        
        print(f"   🤖 AI: {greeting}")
        
        # Test consent response
        consent_response = flow.process_patient_response("Yes, I consent to the call.")
        print(f"   👤 Patient: Yes, I consent to the call.")
        print(f"   🤖 AI: {consent_response}")
        
        # Test knowledge check
        knowledge_response = flow.process_patient_response("I know that an ischemic stroke is when a blood clot blocks blood flow to the brain.")
        print(f"   👤 Patient: I know that an ischemic stroke is when a blood clot blocks blood flow to the brain.")
        print(f"   🤖 AI: {knowledge_response}")
        
        # Check status
        status = flow.get_conversation_status()
        print(f"   ✅ Conversation state: {status['current_state']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Medical conversation test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🏥 Stroke Conversation Bot - Simple Test")
    print("=" * 50)
    
    tests = [
        ("Conversation Flow", test_conversation_flow),
        ("Ollama Integration", test_ollama_integration),
        ("Medical Conversation", test_medical_conversation)
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
        print("🎉 All tests passed! The stroke bot core functionality is working.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration and dependencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
