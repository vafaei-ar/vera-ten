#!/usr/bin/env python3
"""
Setup Validation Script

Validates that all components are properly installed and configured.
"""

import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Check Python version."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.10+)")
        return False

def check_conda_environment():
    """Check if we're in the vten conda environment."""
    print("🔧 Checking conda environment...")
    try:
        result = subprocess.run(['conda', 'info', '--envs'], capture_output=True, text=True)
        if 'vten' in result.stdout and '*' in result.stdout:
            print("   ✅ In vten conda environment")
            return True
        else:
            print("   ❌ Not in vten conda environment")
            print("   💡 Run: conda activate vten")
            return False
    except FileNotFoundError:
        print("   ❌ Conda not found")
        return False

def check_ollama():
    """Check if Ollama is installed and running."""
    print("🤖 Checking Ollama...")
    try:
        # Check if ollama command exists
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Ollama is installed and running")
            
            # Check for required models
            models = result.stdout
            required_models = ['llama3.2:3b', 'mistral:7b', 'phi3:mini']
            for model in required_models:
                if model in models:
                    print(f"   ✅ Model {model} available")
                else:
                    print(f"   ⚠️  Model {model} not found")
            return True
        else:
            print("   ❌ Ollama not responding")
            print("   💡 Run: ollama serve")
            return False
    except FileNotFoundError:
        print("   ❌ Ollama not installed")
        print("   💡 Install from: https://ollama.ai")
        return False

def check_python_packages():
    """Check if required Python packages are installed."""
    print("📦 Checking Python packages...")
    
    required_packages = [
        'ollama', 'pyyaml', 'pyaudio', 'numpy', 'scipy',
        'librosa', 'soundfile', 'webrtcvad', 'speechrecognition',
        'pyttsx3', 'gTTS', 'fastapi', 'uvicorn', 'websockets',
        'pandas', 'openpyxl', 'loguru', 'rich'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"   💡 Install missing packages: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_audio_hardware():
    """Check if audio hardware is available."""
    print("🎤 Checking audio hardware...")
    try:
        import pyaudio
        audio = pyaudio.PyAudio()
        
        device_count = audio.get_device_count()
        if device_count > 0:
            print(f"   ✅ {device_count} audio devices found")
            
            # Check for input devices
            input_devices = []
            for i in range(device_count):
                info = audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    input_devices.append(info['name'])
            
            if input_devices:
                print(f"   ✅ {len(input_devices)} input devices available")
            else:
                print("   ⚠️  No input devices found")
            
            audio.terminate()
            return True
        else:
            print("   ❌ No audio devices found")
            return False
    except Exception as e:
        print(f"   ❌ Audio check failed: {e}")
        return False

def check_project_structure():
    """Check if project structure is correct."""
    print("📁 Checking project structure...")
    
    required_dirs = [
        'conversation_engine',
        'extensions/ollama_medical',
        'recording',
        'config',
        'scripts',
        'data',
        'logs'
    ]
    
    required_files = [
        'main.py',
        'requirements.txt',
        'conversation_engine/__init__.py',
        'extensions/ollama_medical/__init__.py',
        'recording/__init__.py',
        'config/stroke_bot_config.py'
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"   ✅ {dir_path}/")
        else:
            print(f"   ❌ {dir_path}/ (missing)")
            all_good = False
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (missing)")
            all_good = False
    
    return all_good

def check_yaml_file():
    """Check if stroke_sen1.yml exists."""
    print("📋 Checking YAML configuration...")
    
    yaml_path = Path("../stroke_sen1.yml")
    if yaml_path.exists():
        print("   ✅ stroke_sen1.yml found")
        
        # Try to parse it
        try:
            import yaml
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if 'flow' in data and 'meta' in data:
                print("   ✅ YAML structure valid")
                return True
            else:
                print("   ❌ YAML structure invalid")
                return False
        except Exception as e:
            print(f"   ❌ YAML parsing failed: {e}")
            return False
    else:
        print("   ❌ stroke_sen1.yml not found")
        return False

def check_permissions():
    """Check file permissions."""
    print("🔐 Checking permissions...")
    
    # Check if we can write to data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    test_file = data_dir / "test_write.tmp"
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        test_file.unlink()
        print("   ✅ Write permissions OK")
        return True
    except Exception as e:
        print(f"   ❌ Write permissions failed: {e}")
        return False

def run_quick_test():
    """Run a quick functionality test."""
    print("🧪 Running quick test...")
    
    try:
        # Test basic imports first
        import ollama
        import yaml
        import pyaudio
        print("   ✅ Basic packages import successfully")
        
        # Test Ollama connection
        client = ollama.Client()
        models = client.list()
        if models and 'models' in models:
            print("   ✅ Ollama connection works")
        else:
            print("   ⚠️  Ollama connection issue")
        
        # Test YAML parsing
        with open("../stroke_sen1.yml", 'r') as f:
            data = yaml.safe_load(f)
        if 'flow' in data and 'meta' in data:
            print("   ✅ YAML parsing works")
        else:
            print("   ⚠️  YAML parsing issue")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Quick test failed: {e}")
        return False

def main():
    """Main validation function."""
    print("🏥 Stroke Conversation Bot - Setup Validation")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Conda Environment", check_conda_environment),
        ("Ollama", check_ollama),
        ("Python Packages", check_python_packages),
        ("Audio Hardware", check_audio_hardware),
        ("Project Structure", check_project_structure),
        ("YAML Configuration", check_yaml_file),
        ("Permissions", check_permissions),
        ("Quick Test", run_quick_test)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"   ❌ {check_name} check crashed: {e}")
            results.append((check_name, False))
        print()
    
    # Print summary
    print("=" * 50)
    print("📊 Validation Summary:")
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {check_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 Setup validation complete! The stroke bot is ready to use.")
        print("\n🚀 To start a conversation:")
        print("   python main.py --interactive --patient-name 'Test Patient'")
        return 0
    else:
        print(f"\n⚠️  {total - passed} checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
