#!/usr/bin/env python3
"""
Test script to verify Google Cloud setup
Run this before starting the main application
"""

import os
from dotenv import load_dotenv

def test_environment():
    load_dotenv()
    
    print("🧪 Testing Google Cloud Setup...")
    print("=" * 50)
    
    # Check environment variables
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT not set in .env")
        return False
        
    if not creds_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set in .env")
        return False
        
    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found: {creds_path}")
        return False
        
    print(f"✅ Project ID: {project_id}")
    print(f"✅ Credentials file: {creds_path}")
    
    # Test Google Cloud imports
    try:
        from google.cloud import speech
        from google.cloud import language_v1
        print("✅ Google Cloud libraries imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Run: pip install -r requirements.txt")
        return False
    
    # Test API clients
    try:
        speech_client = speech.SpeechClient()
        language_client = language_v1.LanguageServiceClient()
        print("✅ API clients created successfully")
        print("✅ Authentication working!")
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        print("Check your service account key and permissions")
        return False
    
    print("\n🎉 All tests passed! Your setup is ready.")
    return True

if __name__ == "__main__":
    test_environment()