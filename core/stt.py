# ============================================================
# JARVIS — Speech-to-Text Module (core/stt.py)
# ============================================================
# Captures voice input via microphone and converts it to text
# using Google's free Speech-to-Text service.
# ============================================================
# -- PyAudio compatibility shim ------------------------------------
# PyAudioWPatch is a maintained fork that works on Python 3.14+
# but installs as 'pyaudiowpatch' instead of 'pyaudio'.
# SpeechRecognition expects 'import pyaudio', so we register the shim.
import sys
try:
    import pyaudio  # noqa: F401 — standard PyAudio
except ImportError:
    try:
        import pyaudiowpatch as pyaudio  # noqa: F401
        sys.modules['pyaudio'] = pyaudio
        print("[STT] Using PyAudioWPatch as pyaudio shim.")
    except ImportError:
        print("[STT] WARNING: No PyAudio found. Microphone will not work.")

import speech_recognition as sr

# ── Module-level recognizer (reused across calls) ────────────
_recognizer = sr.Recognizer()

# Tweak recognizer settings for better pickup
_recognizer.energy_threshold = 300        # Sensitivity to speech
_recognizer.dynamic_energy_threshold = True
_recognizer.pause_threshold = 1.0         # Seconds of silence to end capture


def listen(status_callback=None) -> str:
    """
    Listens via the default microphone and returns transcribed text.

    Args:
        status_callback: Optional function(status_str) called to update
                         the GUI/terminal with current state.

    Returns:
        Transcribed text string. Empty string "" if nothing was captured
        or if recognition failed.

    Raises:
        OSError: If no microphone is found on the system.
    """
    try:
        with sr.Microphone() as source:
            # Calibrate for ambient noise
            if status_callback:
                status_callback("Calibrating...")
            _recognizer.adjust_for_ambient_noise(source, duration=1)

            # Listen for speech
            if status_callback:
                status_callback("Listening...")
            print("\n🎤 Listening... (speak now)")

            audio = _recognizer.listen(source, timeout=10, phrase_time_limit=15)

            # Transcribe via Google STT
            if status_callback:
                status_callback("Transcribing...")
            print("📝 Transcribing...")

            text = _recognizer.recognize_google(audio)
            print(f"✓  You said: \"{text}\"")
            return text.strip()

    except sr.WaitTimeoutError:
        print("⏱  No speech detected (timeout). Listening again...")
        return ""

    except sr.UnknownValueError:
        print("❓ Could not understand the audio. Try speaking more clearly.")
        return ""

    except sr.RequestError as e:
        print(f"🌐 Google STT service error: {e}")
        print("   Check your internet connection and try again.")
        return ""

    except OSError as e:
        error_msg = (
            f"🎤 Microphone error: {e}\n"
            "   Make sure a microphone is connected and enabled.\n"
            "   On Windows: Check Settings > Privacy > Microphone.\n"
            "   Also ensure PyAudio is installed: pip install pyaudio\n"
            "   If pip fails on Windows, try: pip install pipwin && pipwin install pyaudio"
        )
        print(error_msg)
        raise OSError(error_msg) from e

    except Exception as e:
        print(f"⚠  Unexpected STT error: {e}")
        return ""


def test_microphone() -> bool:
    """
    Quick test to verify the microphone is accessible.
    Returns True if microphone is working, False otherwise.
    """
    try:
        with sr.Microphone() as source:
            print("[OK] Microphone detected and accessible.")
            _recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print(f"  Energy threshold: {_recognizer.energy_threshold:.0f}")
            return True
    except OSError as e:
        print(f"✗ Microphone not accessible: {e}")
        return False


# ── Self-test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  JARVIS STT — Microphone Test")
    print("=" * 50)

    if test_microphone():
        print("\nSay something to test transcription...")
        result = listen()
        if result:
            print(f"\n✓ Successfully transcribed: \"{result}\"")
        else:
            print("\n✗ No transcription returned.")
    else:
        print("\nFix microphone issues before running JARVIS.")
