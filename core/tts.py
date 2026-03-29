"""
================================================================================
JARVIS — Text-to-Speech Module (core/tts.py)
================================================================================
The Voice Layer: Cloud & Offline Speech Generation

Jarvis speaks through a hybrid two-tier TTS system:
1. Primary (Murf Falcon): High-fidelity, emotional AI voices via cloud API.
2. Fallback (pyttsx3): Local, offline, 'robotic' voice if the internet 
   or API keys are unavailable.

Audio feedback is rendered through the Pygame-CE mixer for smooth playback.
================================================================================
"""

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

# ------------------------------------------------------------------------------
# AUDIO DRIVER (PYGAME)
# ------------------------------------------------------------------------------
# Pygame's mixer is the most reliable way to play MP3 streams in Python
# while maintaining the ability to check 'get_busy()' during playback.
_pygame_available = False
try:
    import pygame
    # Initializing with voice-specific frequency (Murf default is 24kHz)
    pygame.mixer.init(frequency=24000, size=-16, channels=1)
    _pygame_available = True
except Exception as e:
    print(f"[TTS] Driver Warning: Pygame mixer init failed ({e}). Audio disabled.")

# ------------------------------------------------------------------------------
# FALLBACK ENGINE (PYTTSX3)
# ------------------------------------------------------------------------------
# An offline SAPI5/NSSS engine that works without internet or API keys.
_pyttsx3_available = False
_pyttsx3_engine = None
try:
    import pyttsx3
    _pyttsx3_engine = pyttsx3.init()
    if _pyttsx3_engine:
        # Configuring for better clarity
        _pyttsx3_engine.setProperty('rate', 170)
        _pyttsx3_engine.setProperty('volume', 1.0)
        _pyttsx3_available = True
except Exception as e:
    print(f"[TTS] Fallback Warning: pyttsx3 init failed ({e}). Offline voice disabled.")

# Global Mute State (Toggled by GUI)
_muted = False


def get_tts_status() -> str:
    """
    Determines the current active speech strategy based on available resources.
    
    Returns:
        str: A descriptive status for display in the terminal or GUI.
    """
    has_murf = bool(MURF_API_KEY and len(MURF_API_KEY) > 10)

    if has_murf and _pygame_available:
        return (f"VOICE: Premium (Murf-API) | Speaker: {MURF_VOICE_ID}\n"
                f"STATUS: Systems Optimal")
    elif _pyttsx3_available:
        return ("VOICE: Fallback (Offline-OS)\n"
                "STATUS: Missing credentials or internet")
    else:
        return ("VOICE: Text-Only\n"
                "STATUS: NO AUDIO DRIVERS INSTALLED")


def set_muted(muted: bool) -> None:
    """External hook for the GUI to toggle audio output."""
    global _muted
    _muted = muted
    print(f"[TTS] Audio output {'silenced' if muted else 'restored'}.")


def is_muted() -> bool:
    """Checks if audio is currently suppressed."""
    return _muted


def _clean_for_tts(text: str) -> str:
    """
    Removes system action tags before text is read aloud.
    Prevents Jarvis from saying things like "bracket action open url bracket".
    """
    cleaned = re.sub(r'\[(?:ACTION|REMINDER|SCHEDULE):[^\]]*\]', '', text)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    return cleaned


def _speak_murf(text: str) -> bool:
    """
    POSTs text to Murf.ai, downloads the MP3 result, and plays it.
    
    Returns:
        bool: True if the entire cloud pipeline succeeded.
    """
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # 1. API Synthesis Request
    url = "https://api.murf.ai/v1/speech/generate"
    headers = {"Content-Type": "application/json", "api-key": MURF_API_KEY}
    payload = {
        "voiceId": MURF_VOICE_ID, "style": MURF_STYLE, "text": text,
        "modelVersion": MURF_MODEL_VERSION, "format": MURF_FORMAT,
        "sampleRate": MURF_SAMPLE_RATE, "channelType": "MONO"
    }

    try:
        print("🔊 [TTS] Synthesis: Sending text to Murf AI...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code != 200: return False

        audio_url = response.json().get("audioFile")
        if not audio_url: return False

        # 2. Synchronous Buffer Download
        print("📥 [TTS] Protocol: Downloading interactive speech buffer...")
        audio_response = requests.get(audio_url, timeout=30)
        if audio_response.status_code != 200: return False

        # 3. Persistence & Playback
        audio_path = str(TEMP_AUDIO_FILE)
        with open(audio_path, "wb") as f:
            f.write(audio_response.content)

        if _pygame_available:
            return _play_with_pygame(audio_path)
        return False

    except Exception as e:
        print(f"[TTS] Premium Pipeline Glitch: {e}")
        return False


def _play_with_pygame(audio_path: str) -> bool:
    """
    Renders audio file through the OS speakers and blocks until done.
    
    CRITICAL: This blocking is what prevents Jarvis from hearing himself!
    """
    try:
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()

        # Monitoring loop: Wait for audio stream to reach EOF
        clock = pygame.time.Clock()
        while pygame.mixer.music.get_busy():
            clock.tick(10)  # Pulse check 10 times per second

        # Anti-aliasing silence buffer
        time.sleep(0.2)
        return True
    except Exception as e:
        print(f"[TTS] Playback Error: {e}")
        return False


def _speak_pyttsx3(text: str) -> bool:
    """Local OS voice engine (no internet required)."""
    global _pyttsx3_engine
    if not _pyttsx3_available or not _pyttsx3_engine:
        return False

    try:
        print("🔊 [TTS] Legacy fallback: Accessing system voices...")
        _pyttsx3_engine.say(text)
        _pyttsx3_engine.runAndWait() # Synchronous play
        return True
    except Exception as e:
        print(f"[TTS] Legacy engine failed: {e}")
        return False


def speak(text: str, status_callback=None) -> None:
    """
    The unified public interface for all Jarvis speech.
    Automatically handles cleaning, muting, and failover logic.
    """
    if not text or not text.strip(): return

    # Cleanup logic
    speech_text = _clean_for_tts(text)
    if not speech_text: return

    # Suppression logic
    if _muted:
        print(f"🔇 [SILENCED] Jarvis: {speech_text}")
        return

    if status_callback: status_callback("Speaking...")

    # Strategy 1: Premium API
    success = _speak_murf(speech_text)

    # Strategy 2: Local Fallback
    if not success:
        print("[TTS] Cloud failover — switching to local OS voice engine.")
        success = _speak_pyttsx3(speech_text)

    # Strategy 3: Visual Only
    if not success:
        print(f"\n💬 [SILENT] Jarvis: {speech_text}\n")

    if status_callback: status_callback("Online")


def speak_startup_greeting(status_callback=None) -> None:
    """Standardized boot-up sequence audio."""
    greeting = "Systems verified. Good to have you back, Bro. How can I assist you today?"
    speak(greeting, status_callback)


# ------------------------------------------------------------------------------
# MODULE TESTING
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print("-" * 60)
    print(" JARVIS Speech Stack — Diagnostic")
    print("-" * 60)
    print(get_tts_status())
    print("-" * 60)
    speak("Diagnostic test initiated. Audio frequency: 0.1 Megahertz.")
