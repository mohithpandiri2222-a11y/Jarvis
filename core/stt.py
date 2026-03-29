"""
================================================================================
JARVIS — Speech-to-Text Module (core/stt.py)
================================================================================
The Hearing Layer: Microphone Capture & Transcription

This module captures analog audio from the local microphone and transcribes 
it into digital text using Google's Speech-to-Text engine.

Key Technical Components:
1. PyAudio: Native audio stream interface.
2. SpeechRecognition: High-level wrapper for STT services.
3. PyAudioWPatch: Fallback shim for modern Python versions on Windows.
================================================================================
"""

import sys

# ------------------------------------------------------------------------------
# PY-AUDIO COMPATIBILITY SHIM
# ------------------------------------------------------------------------------
# Modern Python (3.11+) often struggles with the legacy 'pyaudio' package.
# We prioritize 'pyaudiowpatch' which provides a more robust interface.
try:
    import pyaudio  # Standard installation attempt
except ImportError:
    try:
        import pyaudiowpatch as pyaudio
        # We manually register it into sys.modules so 'speech_recognition'
        # can find it under the standard 'pyaudio' name.
        sys.modules['pyaudio'] = pyaudio
        print("[STT] Compatibility Layer: PyAudioWPatch successfully shimmed.")
    except ImportError:
        print("[STT] CRITICAL: No audio driver detected. Microphone access disabled.")

import speech_recognition as sr

# ------------------------------------------------------------------------------
# RECOGNIZER CONFIGURATION
# ------------------------------------------------------------------------------
_recognizer = sr.Recognizer()

# Fine-tuning the acoustics
# energy_threshold: Minimum volume to start recording (higher = less sensitive)
_recognizer.energy_threshold = 300
_recognizer.dynamic_energy_threshold = True
# pause_threshold: Duration (seconds) of silence before speech is 'finished'
_recognizer.pause_threshold = 1.0


def listen(status_callback=None) -> str:
    """
    Spawns a microphone listener, captures speech, and transcribes it.
    
    This is a blocking call that waits for speech to begin and then finish.
    
    Args:
        status_callback (callable): UI hook to notify user of state changes 
                                   (e.g., 'Listening...', 'Thinking...')
                                   
    Returns:
        str: Transcribed text in lowercase, or empty string if failed.
    """
    try:
        with sr.Microphone() as source:
            # 1. Environment Calibration
            if status_callback: status_callback("Calibrating...")
            # We sample the ambient noise level to distinguish Jarvis's voice
            _recognizer.adjust_for_ambient_noise(source, duration=1)

            # 2. Audio Capture
            if status_callback: status_callback("Listening...")
            print("\n🎤 [HARDWARE] Mic Active — Speak now...")

            # listen() blocks until silence detected or timeout reached
            audio = _recognizer.listen(source, timeout=10, phrase_time_limit=15)

            # 3. Cloud Transcription
            if status_callback: status_callback("Transcribing...")
            print("📝 [CLOUD] Transcribing audio via Google STT...")

            # recognize_google is a free, no-key-required utility for testing
            text = _recognizer.recognize_google(audio)
            print(f"✓  [INPUT] Transcribed: \"{text}\"")
            return text.strip()

    except sr.WaitTimeoutError:
        print("⏱  [TIMEOUT] No speech detected within the window.")
        return ""

    except sr.UnknownValueError:
        print("❓ [STT] Audio too faint or unclear to transcribe.")
        return ""

    except sr.RequestError as e:
        print(f"🌐 [CLOUD] Google STT service inaccessible: {e}")
        return ""

    except OSError as e:
        # This usually means the microphone is locked by another app or missing
        error_msg = (
            f"🎤 [HARDWARE] Microphone Access Denied: {e}\n"
            "   Check system privacy settings or hardware connection."
        )
        print(error_msg)
        raise OSError(error_msg) from e

    except Exception as e:
        print(f"⚠  [STT] Unexpected logical error: {e}")
        return ""


def test_microphone() -> bool:
    """
    Validates that the hardware is responsive and accessible.
    
    Returns:
        bool: True if a microphone was successfully opened and calibrated.
    """
    try:
        with sr.Microphone() as source:
            print("[STT] Hardware Diagnostic: Mic detected.")
            _recognizer.adjust_for_ambient_noise(source, duration=0.5)
            return True
    except Exception as e:
        print(f"[STT] Hardware Diagnostic: FAILED. {e}")
        return False


# ------------------------------------------------------------------------------
# MODULE TESTING
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print("-" * 60)
    print(" JARVIS Hearing Stack — Diagnostic")
    print("-" * 60)
    if test_microphone():
        print(" [OK] Waiting for 3 seconds of test speech...")
        result = listen()
        print(f" [RESULT] Transcription: {result if result else '(None)'}")
    else:
        print(" [FAIL] Hardware error detected.")
