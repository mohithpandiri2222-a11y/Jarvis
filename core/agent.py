"""
================================================================================
JARVIS — Agent Lifecycle Module (core/agent.py)
================================================================================
The Conscious Core: Control Loop & Orchestration

This module defines the JarvisAgent class, which ties together the three 
core pillars of the assistant:
1. HEARING (STT)      : Capturing what the user says.
2. THINKING (LLM)     : Deciding how to respond.
3. SPEAKING (TTS)     : Communicating the result.

The agent maintains conversational state and ensures tasks are executed 
in the correct order (Synchronous Voice Pipeline).
================================================================================
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.stt import listen, test_microphone
from core.llm import get_response
from core.tts import speak, speak_startup_greeting, get_tts_status

# ------------------------------------------------------------------------------
# EXIT SEQUENCE CONFIGURATION
# ------------------------------------------------------------------------------
# Keywords that trigger a graceful shutdown of the background agent thread.
EXIT_KEYWORDS = {
    "exit", "quit", "shutdown", "goodbye", "bye", "stop",
    "shut down", "good bye", "bye bye", "turn off", "deactivate"
}


def _is_exit_command(text: str) -> bool:
    """Simple heuristic to detect intent to close."""
    return text.lower().strip() in EXIT_KEYWORDS


class JarvisAgent:
    """
    The Orchestrator. 
    Maintains the state of the session and bridge communication between 
    the Voice logic and the GUI/Terminal view.
    """

    def __init__(self, status_callback=None, message_callback=None):
        """
        Initializes the agent with optional UI hooks.
        
        Args:
            status_callback: Called when state changes (e.g., 'Thinking')
            message_callback: Called when a new message needs to be logged in chat.
        """
        self._status_callback = status_callback
        self._message_callback = message_callback
        
        # Internal memory for the current session's chat history
        self._conversation_history = []
        self._running = False

    def _update_status(self, status: str) -> None:
        """Internal helper to notify the UI of current processor state."""
        print(f"[STATE] {status}")
        if self._status_callback:
            try:
                self._status_callback(status)
            except Exception:
                pass # UI failures should not kill the brain

    def _add_message(self, role: str, text: str) -> None:
        """Internal helper to append messages to the visual log."""
        if self._message_callback:
            try:
                self._message_callback(role, text)
            except Exception:
                pass

    def stop(self) -> None:
        """Instruction to terminate the main loop after current task finish."""
        self._running = False

    def run(self) -> None:
        """
        The Main Cognitive Loop. 
        Synchronous and infinite until stopped.
        
        Pipeline Architecture:
        1. Listen (Blocks until silence)
        2. Think  (Blocks until API response)
        3. Speak  (Blocks until audio finished)
        """
        self._running = True

        print("\n" + "=" * 60)
        print("  JARVIS INFRASTRUCTURE — OPERATIONAL")
        print("=" * 60 + "\n")

        # Log system status (TTS engine, etc.)
        print(get_tts_status())
        print()

        # 1. INITIALIZATION GREETING
        self._update_status("Calibrating Core...")
        speak_startup_greeting(self._status_callback)
        self._add_message("jarvis", "All systems online. Ready to assist, Bro.")

        # 2. THE SENSORY LOOP
        while self._running:
            try:
                # -- PHASE 1: Perception (Listen) --
                self._update_status("Awaiting Command...")
                user_text = listen(self._status_callback)

                # Ignore empty captures (ambient noise glitches)
                if not user_text:
                    continue

                # Check for termination intent
                if _is_exit_command(user_text):
                    self._update_status("Deactivating...")
                    shutdown_msg = "Powering down. Good day, Bro."
                    self._add_message("user", user_text)
                    self._add_message("jarvis", shutdown_msg)
                    speak(shutdown_msg, self._status_callback)
                    break

                # -- PHASE 2: Cognition (Think) --
                # Update visual log immediately
                self._add_message("user", user_text)
                
                self._update_status("Thinking...")
                response_text, self._conversation_history = get_response(
                    user_text,
                    self._conversation_history,
                    self._status_callback,
                )

                # -- PHASE 3: Projection (Speak) --
                self._add_message("jarvis", response_text)
                self._update_status("Projecting Voice...")
                speak(response_text, self._status_callback)

                # Reset state for next interaction
                self._update_status("Online")

            except KeyboardInterrupt:
                print("\n[SYSTEM] Manual interrupt signal received.")
                break

            except OSError as mic_err:
                # Critical hardware failure
                print(f"[FATAL] Audio sensory loss: {mic_err}")
                self._update_status("HARDWARE ERROR")
                break

            except Exception as e:
                # Non-critical logic error (likely API timeout or JSON parse fail)
                print(f"[RECOVER] Logical fault in loop: {e}")
                self._update_status("Error Recovery...")
                # Feedback to user so they don't think Jarvis is dead
                try:
                    speak("Minor cognitive hitch Bro, I'm recalculating.", self._status_callback)
                except:
                    pass
                continue

        # Shutdown sequence
        self._running = False
        self._update_status("Offline")
        print("\n[JARVIS] Agent decommissioned. Goodbye.")


def run_terminal_mode() -> None:
    """
    Simplistic runner for CLI-only environments.
    No GUI requirements, just pure voice pipeline.
    """
    print("[INIT] Booting Jarvis (CLI/Headless Mode)...")

    # Final hardware sanity check before entering the loop
    if not test_microphone():
        print("[INIT] Error: Microphone hardware not responsive. Terminating.")
        sys.exit(1)

    agent = JarvisAgent()
    agent.run()


# ------------------------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    run_terminal_mode()
