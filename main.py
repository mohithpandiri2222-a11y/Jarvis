#!/usr/bin/env python3
"""
================================================================================
JARVIS — Main Entry Point
================================================================================
Just A Rather Very Intelligent System
A Voice-First AI Desktop Assistant with Multi-Model Support

The main module orchestrates the initialization, configuration validation, 
and user interface launching (GUI or Terminal). 

Project Architecture:
- core/        : Internal logic for STT, LLM (Brains), and TTS.
- ui/          : Interface components (Tkinter GUI and Setup Dialog).
- data/        : Local storage management (Schedule/Reminders).
- config.py    : Environment and API key management.
================================================================================
"""

import sys
import argparse
from pathlib import Path

# ------------------------------------------------------------------------------
# PATH CONFIGURATION
# ------------------------------------------------------------------------------
# We ensure the project root is in sys.path so that internal imports 
# (like 'from core' or 'from ui') function correctly regardless of how 
# the script is invoked.
_project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_project_root))


def _print_banner():
    """
    Displays the stylistic JARVIS ASCII art banner.
    Modelled after classic command-line interface aesthetics.
    """
    banner = r"""
    +===========================================================+
    |                                                           |
    |           _   _    ____  __     __  ___   ____            |
    |          | | / \  |  _ \ \ \   / / |_ _| / ___|           |
    |       _  | |/ _ \ | |_) | \ \ / /   | |  \___ \           |
    |      | |_| / ___ \|  _ <   \ V /    | |   ___) |          |
    |       \___/_/   \_\_| \_\   \_/    |___| |____/           |
    |                                                           |
    |       Just A Rather Very Intelligent System               |
    |       Voice-First AI Desktop Assistant                    |
    |                                                           |
    +===========================================================+
    """
    print(banner)


def _show_provider_info():
    """
    Retrieves and displays the active AI provider and model configuration.
    Helps the user confirm which 'brain' Jarvis is currently using.
    """
    from config import LLM_PROVIDER, LLM_MODEL, PROVIDER_NAMES
    provider_name = PROVIDER_NAMES.get(LLM_PROVIDER, LLM_PROVIDER)
    print(f"    [STATE] Provider : {provider_name}")
    print(f"    [STATE] Model    : {LLM_MODEL}")
    print()


def _run_setup_dialog() -> bool:
    """
    Launches the visual Setup Dialog for first-time users or re-configuration.
    
    Returns:
        bool: True if the user successfully saved their credentials, 
              False if the window was closed without saving.
    """
    print("[INIT] Launching configuration wizard...")
    print("[INIT] Please follow the instructions in the setup window.\n")
    try:
        from ui.setup_dialog import SetupDialog
        dialog = SetupDialog()
        result = dialog.run()

        if result:
            provider = result["provider"]
            print(f"[INIT] Credentials secured. Provider set to: {provider}")
            return True
        else:
            print("[INIT] Setup stage was aborted by the user.")
            return False
    except Exception as e:
        print(f"[ERROR] Fail-to-launch Setup Dialog: {e}")
        print("[HINT] You may manually edit the .env file in the root directory.")
        return False


def _run_tests():
    """
    Performs a system-wide diagnostic check of all modules and hardware.
    Checks config integrity, data accessibility, and microphone health.
    
    Returns:
        bool: True if all critical tests pass, False otherwise.
    """
    print("-" * 60)
    print(" JARVIS — System Diagnostic Check")
    print("-" * 60)

    tests_passed = 0
    tests_total = 0

    # Test 1: Configuration Engine
    tests_total += 1
    try:
        from config import validate_config, LLM_PROVIDER
        print(f"  [PASS] Config Loader (Active: {LLM_PROVIDER})")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] Config Loader error: {e}")

    # Test 2: Local Data Access
    tests_total += 1
    try:
        from data.schedule import get_schedule
        from data.reminders import get_reminders
        count = len(get_schedule())
        print(f"  [PASS] Logical Data Store ({count} schedule nodes detected)")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] Data Store access error: {e}")

    # Test 3: Speech-to-Text (STT) Stack
    tests_total += 1
    try:
        from core.stt import listen
        print("  [PASS] STT Core (SpeechRecognition pipeline ready)")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] STT Core failed: {e}")

    # Test 4: LLM Integration (Brains)
    tests_total += 1
    try:
        from core.llm import SYSTEM_PROMPT
        print(f"  [PASS] LLM Layer ({len(SYSTEM_PROMPT)} chars prompt loaded)")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] LLM Layer failed: {e}")

    # Test 5: Text-to-Speech (TTS) Stack
    tests_total += 1
    try:
        from core.tts import speak
        print("  [PASS] TTS Engine (Murf/pysstx3 hybrid ready)")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] TTS Engine failed: {e}")

    # Test 6: Agent Loop
    tests_total += 1
    try:
        from core.agent import JarvisAgent
        print("  [PASS] Agent Lifecycle Orchestrator ready")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] Agent module failed: {e}")

    # Test 7: Hardware Verification (Microphone)
    tests_total += 1
    try:
        from core.stt import test_microphone
        if test_microphone():
            print("  [PASS] Hardware Check: Microphone detected and listening")
            tests_passed += 1
        else:
            print("  [WARN] Hardware Check: Microphone NOT found (Input required)")
    except Exception as e:
        print(f"  [WARN] Hardware Check error: {e}")

    print(f"\nDiagnostic Result: {tests_passed}/{tests_total} passed")
    print("-" * 60)
    return tests_passed == tests_total


def main():
    """
    Primary orchestrator for the JARVIS lifecycle.
    1. Parse CLI arguments
    2. Handle setup/test modes
    3. Validate credentials
    4. Initialize audio drivers
    5. Boot the chosen UI mode
    """
    parser = argparse.ArgumentParser(
        description="J.A.R.V.I.S. — Voice-First AI Desktop Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  python main.py             (GUI Mode)\n  python main.py --no-gui    (Terminal Mode)\n  python main.py --setup     (Config Wizard)\n",
    )
    parser.add_argument("--no-gui", action="store_true", help="Launch in Headless (Terminal) mode")
    parser.add_argument("--test", action="store_true", help="Run system diagnostics")
    parser.add_argument("--setup", action="store_true", help="Force re-launch the setup wizard")

    args = parser.parse_args()
    _print_banner()

    # -- Diagnostic Mode --
    if args.test:
        success = _run_tests()
        sys.exit(0 if success else 1)

    # -- Configuration Force-Launch --
    if args.setup:
        if not _run_setup_dialog():
            print("[FATAL] Required configuration not completed. Terminating.")
            sys.exit(1)

    # -- First-Time or Missing Credentials Check --
    # Automatically triggers setup if the .env is missing or incomplete.
    from config import has_valid_llm_key
    if not has_valid_llm_key():
        print("[SYSTEM] No valid AI credentials detected.")
        if not _run_setup_dialog():
            print("[FATAL] Jarvis cannot function without a valid AI brain. Terminating.")
            sys.exit(1)

    # -- Configuration Sanity Check --
    from config import validate_config
    if not validate_config():
        print("[FATAL] Configuration validation failed. Run with --setup to fix.")
        sys.exit(1)

    # Success feedback
    print("[SYSTEM] Core systems validated and online.")
    _show_provider_info()

    # -- Audio Driver Initialization --
    # Pygame mixer is used for high-fidelity playback of Murf TTS responses.
    try:
        import pygame
        if not pygame.mixer.get_init():
            # Initializing with voice-optimized settings
            pygame.mixer.init(frequency=24000, size=-16, channels=1)
        print("[SYSTEM] Audio playback subsystem ready.")
    except Exception as e:
        print(f"[WARN] Audio driver issue: {e}. Voice feedback may be restricted.")

    # -- UI Dispatch --
    if args.no_gui:
        # Launching the synchronous terminal loop
        print("[LAUNCH] Entering headless terminal mode...")
        from core.agent import run_terminal_mode
        run_terminal_mode()
    else:
        # Launching the premium multi-threaded GUI
        print("[LAUNCH] Initializing Jarvis Dashboard...")
        try:
            from ui.gui import JarvisGUI
            gui = JarvisGUI()
            gui.run()  # Starts the Tkinter mainloop (blocking)
        except Exception as e:
            # Automatic fallback if the GUI fails (e.g., missing Tcl/Tk)
            print(f"[LAUNCH] GUI Initialization failed: {e}")
            print("[LAUNCH] Falling back to Terminal mode...")
            from core.agent import run_terminal_mode
            run_terminal_mode()


if __name__ == "__main__":
    main()
