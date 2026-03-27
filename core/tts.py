# ============================================================
# JARVIS — Text-to-Speech Module (core/tts.py)
# ============================================================
# Converts text to speech using Murf Falcon API (primary)
# with pyttsx3 as a local fallback. Handles audio download
# and playback via pygame.
# ============================================================

import os
import re
import time
import requests

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    MURF_API_KEY,
    MURF_VOICE_ID,
    MURF_MODEL_VERSION,
    MURF_STYLE,
    MURF_SAMPLE_RATE,
    MURF_FORMAT,
    TEMP_AUDIO_FILE,
    AUDIO_DIR,
)

# -- Pygame Initialization ----------------------------------------
_pygame_available = False
try:
    import pygame
    pygame.mixer.init(frequency=24000, size=-16, channels=1)
    _pygame_available = True
except Exception as e:
    print(f"[TTS] WARNING: pygame mixer init failed: {e}")
    print("[TTS] Audio playback will NOT work.")

# -- pyttsx3 Fallback ---------------------------------------------
_pyttsx3_available = False
_pyttsx3_engine = None
try:
    import pyttsx3
    _pyttsx3_engine = pyttsx3.init()
    if _pyttsx3_engine is None:
        raise RuntimeError("pyttsx3.init() returned None")
    _pyttsx3_engine.setProperty('rate', 170)    # Slightly slower for clarity
    _pyttsx3_engine.setProperty('volume', 1.0)
    _pyttsx3_available = True
except Exception as e:
    _pyttsx3_engine = None
    print(f"[TTS] WARNING: pyttsx3 init failed: {e}")
    print("[TTS] Local fallback TTS will not be available.")

# -- Mute state ---------------------------------------------------
_muted = False


def get_tts_status() -> str:
    """
    Returns a clear string describing which TTS engine is active.
    Call at startup so the user knows what voice they will hear.
    """
    has_murf_key = bool(MURF_API_KEY and MURF_API_KEY != "ap-your-key-here")

    if has_murf_key and _pygame_available:
        return (f"[TTS] ACTIVE ENGINE: Murf Falcon (GEN2) | Voice: {MURF_VOICE_ID}\n"
                f"[TTS] Fallback: {'pyttsx3 (offline)' if _pyttsx3_available else 'text-only (no fallback)'}")
    elif _pyttsx3_available:
        reason = "Missing MURF_API_KEY" if not has_murf_key else "pygame not available"
        return (f"[TTS] WARNING: Using OFFLINE pyttsx3 voice (robotic). Reason: {reason}\n"
                f"[TTS] To use Murf Falcon, fix the issue above and restart.")
    else:
        return ("[TTS] CRITICAL: No TTS engine available! Voice will be TEXT-ONLY.\n"
                "[TTS] Install pygame-ce and add MURF_API_KEY to .env")


def set_muted(muted: bool) -> None:
    """Enable or disable audio output."""
    global _muted
    _muted = muted
    print(f"[TTS] Audio {'muted' if muted else 'unmuted'}")


def is_muted() -> bool:
    """Check if audio is currently muted."""
    return _muted


def _clean_for_tts(text: str) -> str:
    """
    Strips any remaining action tags and cleans text for TTS.
    """
    # Remove all [ACTION:...], [REMINDER:...], [SCHEDULE:...] tags
    cleaned = re.sub(r'\[(?:ACTION|REMINDER|SCHEDULE):[^\]]*\]', '', text)
    # Remove multiple spaces
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    return cleaned


def _speak_murf(text: str) -> bool:
    """
    Sends text to Murf Falcon API and plays the returned audio.

    Returns True if successful, False if failed (so we can fallback).
    """
    # Ensure audio directory exists
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # ── API Request ──────────────────────────────────────────
    url = "https://api.murf.ai/v1/speech/generate"
    headers = {
        "Content-Type": "application/json",
        "api-key": MURF_API_KEY,
    }
    payload = {
        "voiceId": MURF_VOICE_ID,
        "style": MURF_STYLE,
        "text": text,
        "modelVersion": MURF_MODEL_VERSION,
        "format": MURF_FORMAT,
        "sampleRate": MURF_SAMPLE_RATE,
        "channelType": "MONO",
        "rate": 0,
        "pitch": 0,
    }

    try:
        print("🔊 Generating speech via Murf Falcon...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"[TTS] Murf API error {response.status_code}: {response.text}")
            return False

        data = response.json()
        audio_url = data.get("audioFile")

        if not audio_url:
            print(f"[TTS] Murf response missing audioFile: {data}")
            return False

        # ── Download the audio file ──────────────────────────
        print("📥 Downloading audio...")
        audio_response = requests.get(audio_url, timeout=30)

        if audio_response.status_code != 200:
            print(f"[TTS] Audio download failed: {audio_response.status_code}")
            return False

        # Save to temp file
        audio_path = str(TEMP_AUDIO_FILE)
        with open(audio_path, "wb") as f:
            f.write(audio_response.content)

        # -- Play the audio ----------------------------------------
        if _pygame_available:
            played = _play_with_pygame(audio_path)
            if not played:
                return False  # triggers pyttsx3 fallback
        else:
            print("[TTS] pygame not available. Cannot play audio.")
            return False

        # ── Cleanup ──────────────────────────────────────────
        try:
            os.remove(audio_path)
        except OSError:
            pass  # File might still be in use

        return True

    except requests.exceptions.Timeout:
        print("[TTS] Murf API request timed out.")
        return False
    except requests.exceptions.ConnectionError:
        print("[TTS] Cannot connect to Murf API. Check internet connection.")
        return False
    except Exception as e:
        print(f"[TTS] Murf TTS error: {e}")
        return False


def _play_with_pygame(audio_path: str) -> bool:
    """
    Plays an MP3 file using pygame.mixer and waits until it finishes.
    This is the BLOCKING playback loop required by the spec.

    Returns True if playback succeeded, False if it failed.
    """
    try:
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()

        print("[TTS] Speaking...")

        # CRITICAL: Block until audio finishes playing
        # This prevents the microphone from recording Jarvis's own voice
        clock = pygame.time.Clock()
        while pygame.mixer.music.get_busy():
            clock.tick(10)  # Check 10 times per second

        # Small buffer to ensure clean completion
        time.sleep(0.2)
        return True

    except Exception as e:
        print(f"[TTS] Pygame playback error: {e}")
        return False


def _speak_pyttsx3(text: str) -> bool:
    """
    Fallback: speaks text using pyttsx3 (local, offline TTS).
    Returns True if successful, False otherwise.
    """
    global _pyttsx3_engine, _pyttsx3_available

    if not _pyttsx3_available:
        return False

    # Defensive: re-init if engine was garbage-collected or went stale
    if _pyttsx3_engine is None:
        try:
            _pyttsx3_engine = pyttsx3.init()
            if _pyttsx3_engine is None:
                raise RuntimeError("pyttsx3.init() returned None on re-init")
            _pyttsx3_engine.setProperty('rate', 170)
            _pyttsx3_engine.setProperty('volume', 1.0)
        except Exception as e:
            print(f"[TTS] pyttsx3 re-init failed: {e}")
            _pyttsx3_available = False
            return False

    try:
        print("🔊 Speaking via local TTS (fallback)...")
        _pyttsx3_engine.say(text)
        _pyttsx3_engine.runAndWait()
        return True
    except Exception as e:
        print(f"[TTS] pyttsx3 error: {e}")
        # Engine is broken — clear it so next call attempts re-init
        _pyttsx3_engine = None
        return False


def speak(text: str, status_callback=None) -> None:
    """
    Main TTS function. Converts text to speech and plays it.

    Pipeline:
      1. Clean text (remove action tags)
      2. Try Murf Falcon API (primary)
      3. If Murf fails, fall back to pyttsx3 (local)
      4. If both fail, print the text to console

    Args:
        text: The text to speak.
        status_callback: Optional function(status_str) for GUI updates.
    """
    if not text or not text.strip():
        return

    # Clean the text for TTS
    clean_text = _clean_for_tts(text)
    if not clean_text:
        return

    # Check mute
    if _muted:
        print(f"🔇 [MUTED] Jarvis: {clean_text}")
        return

    if status_callback:
        status_callback("Speaking...")

    # Try Murf Falcon first (primary TTS)
    success = _speak_murf(clean_text)

    if not success:
        print("[TTS] Murf failed. Trying local fallback...")
        success = _speak_pyttsx3(clean_text)

    if not success:
        # Last resort: just print it
        print(f"\n💬 Jarvis (text-only): {clean_text}\n")

    if status_callback:
        status_callback("Ready")


def speak_startup_greeting(status_callback=None) -> None:
    """
    Speaks the startup greeting when JARVIS boots up.
    """
    greeting = "Good to have you back, Bro. All systems are online. What do we need today?"
    speak(greeting, status_callback)


# ── Self-test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  JARVIS TTS — Audio Test")
    print("=" * 50)
    print(f"  Murf Voice : {MURF_VOICE_ID}")
    print(f"  Murf Model : {MURF_MODEL_VERSION}")
    print(f"  Pygame     : {'Available' if _pygame_available else 'Not Available'}")
    print(f"  pyttsx3    : {'Available' if _pyttsx3_available else 'Not Available'}")
    print()

    test_text = "Hello Bro. This is a test of the JARVIS voice system. All systems are functioning normally."
    print(f"  Test text: \"{test_text}\"")
    print()

    speak(test_text)
    print("\n  ✓ TTS test complete.")
