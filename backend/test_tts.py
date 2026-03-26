import sys
import os
import traceback

sys.path.append(r"c:\Users\Rithik\ip_agent\backend")

from app.speech_service import SpeechService

def test():
    try:
        service = SpeechService()
        print("Service initialized. Attempting to synthesize...")
        audio = service.synthesize_speech("Hello, world! This is a test of the text to speech.")
        
        if audio is None:
            print("Failed: audio is None")
        else:
            print(f"Success! Generated {len(audio)} bytes.")
    except Exception as e:
        print("CRASHED:")
        traceback.print_exc()

if __name__ == "__main__":
    test()
