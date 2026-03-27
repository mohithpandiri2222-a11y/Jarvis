#!/usr/bin/env python3
# ============================================================
# JARVIS -- Main Entry Point
# ============================================================
#   J.A.R.V.I.S.
#   Just A Rather Very Intelligent System
#   Voice-First AI Desktop Assistant
#   Powered by GPT-4o + Murf Falcon TTS
#
# Usage:
#   python main.py            Launch with GUI
#   python main.py --no-gui   Terminal-only mode
#   python main.py --test     Run module tests
#
# ============================================================

import sys
import argparse
from pathlib import Path

# Ensure project root is in path
_project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_project_root))


def _print_banner():
    """Prints the JARVIS startup banner."""
    banner = """
    +===========================================================+
    |                                                           |
    |           _   _    ____  __     __  ___   ____            |
    |          | | / \\  |  _ \\ \\ \\   / / |_ _| / ___|       |
    |       _  | |/ _ \\ | |_) | \\ \\ / /   | |  \\___ \\      |
    |      | |_| / ___ \\|  _ <   \\ V /    | |   ___) |        |
    |       \\___/_/   \\_\\_| \\_\\   \\_/    |___| |____/     |
    |                                                           |
    |       Just A Rather Very Intelligent System               |
    |       Voice-First AI Desktop Assistant                    |
    |                                                           |
    |       GPT-4o  |  Murf Falcon TTS  |  Python               |
    |                                                           |
    +===========================================================+
    """
    print(banner)


def _run_tests():
    """Runs quick module import and connectivity tests."""
    print("=" * 55)
    print("  JARVIS -- Module Tests")
    print("=" * 55)

    tests_passed = 0
    tests_total = 0

    # Test 1: Config
    tests_total += 1
    try:
        from config import validate_config, OPENAI_API_KEY, MURF_API_KEY
        print("  [PASS] config.py loaded successfully")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] config.py failed: {e}")

    # Test 2: Data modules
    tests_total += 1
    try:
        from data.schedule import get_schedule, add_event, remove_event
        from data.reminders import add_reminder, get_reminders, delete_reminder
        schedule = get_schedule()
        print(f"  [PASS] data modules loaded ({len(schedule)} schedule entries)")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] data modules failed: {e}")

    # Test 3: STT module
    tests_total += 1
    try:
        from core.stt import listen, test_microphone
        print("  [PASS] core/stt.py loaded successfully")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] core/stt.py failed: {e}")

    # Test 4: LLM module
    tests_total += 1
    try:
        from core.llm import get_response, SYSTEM_PROMPT
        prompt_len = len(SYSTEM_PROMPT)
        print(f"  [PASS] core/llm.py loaded ({prompt_len} char system prompt)")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] core/llm.py failed: {e}")

    # Test 5: TTS module
    tests_total += 1
    try:
        from core.tts import speak, speak_startup_greeting
        print("  [PASS] core/tts.py loaded successfully")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] core/tts.py failed: {e}")

    # Test 6: Agent module
    tests_total += 1
    try:
        from core.agent import JarvisAgent, run_terminal_mode
        print("  [PASS] core/agent.py loaded successfully")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] core/agent.py failed: {e}")

    # Test 7: GUI module
    tests_total += 1
    try:
        from ui.gui import JarvisGUI
        print("  [PASS] ui/gui.py loaded successfully")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] ui/gui.py failed: {e}")

    # Test 8: Microphone check
    tests_total += 1
    try:
        from core.stt import test_microphone
        mic_ok = test_microphone()
        if mic_ok:
            print("  [PASS] Microphone is accessible")
            tests_passed += 1
        else:
            print("  [WARN] Microphone not accessible (JARVIS needs a mic)")
    except Exception as e:
        print(f"  [WARN] Microphone check failed: {e}")

    print()
    print(f"  Results: {tests_passed}/{tests_total} tests passed")

    if tests_passed == tests_total:
        print("  All tests passed! JARVIS is ready to launch.")
    else:
        print("  Some tests failed. Check the errors above.")

    print("=" * 55)
    return tests_passed == tests_total


def main():
    """Main entry point for JARVIS."""
    parser = argparse.ArgumentParser(
        description="JARVIS -- Voice-First AI Desktop Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              Launch with GUI
  python main.py --no-gui     Terminal-only mode
  python main.py --test       Run module tests
        """,
    )
    parser.add_argument(
        "--no-gui", action="store_true",
        help="Run in terminal-only mode (no tkinter window)"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Run module tests and exit"
    )

    args = parser.parse_args()

    # Print the banner
    _print_banner()

    # -- Test mode -------------------------------------------------
    if args.test:
        success = _run_tests()
        sys.exit(0 if success else 1)

    # -- Validate configuration ------------------------------------
    from config import validate_config
    if not validate_config():
        print("[JARVIS] Configuration invalid. Cannot start.")
        print("[JARVIS] Open .env and add your API keys, then try again.")
        sys.exit(1)

    print("[JARVIS] Configuration validated.")
    print()

    # -- Initialize pygame mixer early -----------------------------
    try:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=24000, size=-16, channels=1)
        print("[JARVIS] Audio system initialized.")
    except Exception as e:
        print(f"[JARVIS] Warning: pygame mixer init issue: {e}")
        print("[JARVIS] Audio playback may not work correctly.")

    # -- Launch ----------------------------------------------------
    if args.no_gui:
        # Terminal-only mode
        print("[JARVIS] Launching in terminal mode...")
        print("[JARVIS] Say 'exit', 'quit', or 'goodbye' to stop.\n")
        from core.agent import run_terminal_mode
        run_terminal_mode()
    else:
        # GUI mode
        print("[JARVIS] Launching GUI mode...")
        print("[JARVIS] Close the window or say 'exit' to stop.\n")
        try:
            from ui.gui import JarvisGUI
            gui = JarvisGUI()
            gui.run()  # Blocking -- runs tkinter mainloop
        except ImportError as e:
            print(f"[JARVIS] GUI failed to load: {e}")
            print("[JARVIS] Falling back to terminal mode...")
            from core.agent import run_terminal_mode
            run_terminal_mode()
        except Exception as e:
            print(f"[JARVIS] GUI error: {e}")
            print("[JARVIS] Falling back to terminal mode...")
            from core.agent import run_terminal_mode
            run_terminal_mode()


if __name__ == "__main__":
    main()
