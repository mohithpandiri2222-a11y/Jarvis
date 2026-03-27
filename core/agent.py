# ============================================================
# JARVIS — Agent Module (core/agent.py)
# ============================================================
# The main synchronous execution loop that connects:
#   STT (listen) → LLM (think) → TTS (speak) → repeat
#
# This is the brain of the operation.
# ============================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.stt import listen, test_microphone
from core.llm import get_response
from core.tts import speak, speak_startup_greeting, get_tts_status

# ── Exit keywords ────────────────────────────────────────────
EXIT_KEYWORDS = {"exit", "quit", "shutdown", "goodbye", "bye", "stop",
                 "shut down", "good bye", "bye bye", "turn off"}


def _is_exit_command(text: str) -> bool:
    """Check if the user wants to exit."""
    return text.lower().strip() in EXIT_KEYWORDS


class JarvisAgent:
    """
    The JARVIS Agent — orchestrates the full voice pipeline.

    Usage:
        agent = JarvisAgent()
        agent.run()  # Blocking loop

    Or with GUI callbacks:
        agent = JarvisAgent(
            status_callback=update_status_label,
            message_callback=add_chat_message
        )
        agent.run()
    """

    def __init__(self, status_callback=None, message_callback=None):
        """
        Args:
            status_callback: Optional function(status_str) called when
                             the agent's state changes. Used by the GUI
                             to update the status label.

            message_callback: Optional function(role_str, text_str) called
                              when a message is added to the conversation.
                              role is "user" or "jarvis". Used by the GUI
                              to update the chat log.
        """
        self._status_callback = status_callback
        self._message_callback = message_callback
        self._conversation_history = []
        self._running = False

    def _update_status(self, status: str) -> None:
        """Update status via callback and print to console."""
        print(f"[JARVIS] Status: {status}")
        if self._status_callback:
            try:
                self._status_callback(status)
            except Exception:
                pass  # Don't crash the agent if callback fails

    def _add_message(self, role: str, text: str) -> None:
        """Add a message to the GUI chat log."""
        if self._message_callback:
            try:
                self._message_callback(role, text)
            except Exception:
                pass

    def stop(self) -> None:
        """Signal the agent to stop after the current iteration."""
        self._running = False

    def run(self) -> None:
        """
        Main execution loop. This is BLOCKING and runs forever
        until the user says an exit keyword or stop() is called.

        The loop follows the strict synchronous pipeline:
          1. Listen (blocks until speech detected)
          2. Send to GPT-4o (blocks until response)
          3. Speak response (blocks until audio finishes)
          4. Repeat
        """
        self._running = True

        print()
        print("=" * 60)
        print("    J.A.R.V.I.S. -- ONLINE")
        print("    Just A Rather Very Intelligent System")
        print("=" * 60)
        print()

        # -- Print TTS engine status so user knows what voice they'll hear
        print(get_tts_status())
        print()

        # ── Startup Greeting ─────────────────────────────────
        self._update_status("Starting up...")
        speak_startup_greeting(self._status_callback)
        self._add_message("jarvis",
                          "Good to have you back, Bro. All systems are online. "
                          "What do we need today?")

        # ── Main Loop ────────────────────────────────────────
        while self._running:
            try:
                # STEP 1: Listen for user speech
                self._update_status("Listening...")
                user_text = listen(self._status_callback)

                # No speech detected — loop back
                if not user_text:
                    continue

                # Check for exit command
                if _is_exit_command(user_text):
                    self._update_status("Shutting down...")
                    shutdown_msg = "Shutting down. Good day, Bro."
                    print(f"\n💬 Jarvis: {shutdown_msg}")
                    self._add_message("user", user_text)
                    self._add_message("jarvis", shutdown_msg)
                    speak(shutdown_msg, self._status_callback)
                    break

                # Log the user message
                self._add_message("user", user_text)

                # STEP 2: Send to GPT-4o and get response
                self._update_status("Thinking...")
                response_text, self._conversation_history = get_response(
                    user_text,
                    self._conversation_history,
                    self._status_callback,
                )

                # Log the Jarvis response
                print(f"\n💬 Jarvis: {response_text}")
                self._add_message("jarvis", response_text)

                # STEP 3: Speak the response (BLOCKING)
                self._update_status("Speaking...")
                speak(response_text, self._status_callback)

                # STEP 4: Ready for next input
                self._update_status("Ready")

            except KeyboardInterrupt:
                print("\n\n[JARVIS] Interrupted by user. Shutting down...")
                self._update_status("Shutting down...")
                speak("Interrupted. Shutting down, Bro.", self._status_callback)
                break

            except OSError as e:
                # Microphone error — cannot continue
                print(f"\n[JARVIS] Critical error: {e}")
                self._update_status("Error: Microphone")
                print("[JARVIS] Cannot access microphone. Exiting.")
                break

            except Exception as e:
                # Non-critical error -- speak feedback and continue
                print(f"\n[JARVIS] Error in main loop: {e}")
                self._update_status("Error -- recovering...")
                import traceback
                traceback.print_exc()
                # Tell the user something went wrong instead of going silent
                try:
                    speak("I ran into a small issue Bro, give me a moment.",
                          self._status_callback)
                except Exception:
                    pass  # If even speak fails, just continue
                continue

        self._running = False
        self._update_status("Offline")
        print("\n[JARVIS] Agent stopped. Goodbye.")


def run_terminal_mode() -> None:
    """
    Runs the JARVIS agent in terminal-only mode (no GUI).
    """
    print("[JARVIS] Starting in terminal mode...")
    print("[JARVIS] Say 'exit', 'quit', or 'goodbye' to stop.\n")

    # Quick microphone check
    if not test_microphone():
        print("\n[JARVIS] ERROR: Microphone not available.")
        print("[JARVIS] Fix microphone issues and try again.")
        sys.exit(1)

    agent = JarvisAgent()
    agent.run()


# ── Self-test ────────────────────────────────────────────────
if __name__ == "__main__":
    run_terminal_mode()
