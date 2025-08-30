#!/usr/bin/env python3
"""
Quick test to verify audio transcription with a very short audio file
"""

import requests
import tempfile
import wave
import struct
import math

def create_test_audio(duration_seconds=5, frequency=440):
    """Create a short test audio file"""
    sample_rate = 44100
    frames = int(duration_seconds * sample_rate)
    
    # Create a simple sine wave
    audio_data = []
    for i in range(frames):
        value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        audio_data.append(struct.pack('<h', value))
    
    # Write to temporary WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
        with wave.open(temp_file.name, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(audio_data))
        
        return temp_file.name

def test_transcription_api():
    """Test the transcription API with a short audio file"""
    
    print("🧪 Testing Transcription API...")
    
    # Create test audio (5 seconds of silence/tone)
    audio_file = create_test_audio(5)
    print(f"✅ Created test audio file: {audio_file}")
    
    try:
        # Send to API
        with open(audio_file, 'rb') as f:
            files = {'audio': ('test.wav', f, 'audio/wav')}
            response = requests.post('http://127.0.0.1:5000/api/transcribe', files=files)
        
        print(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            transcription = data.get('transcription', '')
            print(f"✅ Transcription successful: '{transcription}'")
            if not transcription:
                print("ℹ️  Empty transcription (expected for sine wave audio)")
        else:
            print(f"❌ API Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        # Clean up
        import os
        if os.path.exists(audio_file):
            os.unlink(audio_file)
            print(f"🧹 Cleaned up test file")

if __name__ == "__main__":
    test_transcription_api()