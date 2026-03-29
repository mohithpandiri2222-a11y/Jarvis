"""
================================================================================
JARVIS — Configuration Loader
================================================================================
Secure Credential Management & Multi-Provider Config Engine

This module is responsible for:
1. Loading and parsing environment variables (.env).
2. Dynamically switching LLM providers (OpenAI, Claude, Gemini).
3. Validating that the necessary API keys are present at startup.
4. Persisting user setup changes back to the .env file.
================================================================================
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# PATH RESOLUTION
# ------------------------------------------------------------------------------
# We locate the .env in the project root to ensure consistency across 
# different execution environments (IDE vs Terminal).
_project_root = Path(__file__).resolve().parent
_env_path = _project_root / ".env"


def reload_env():
    """
    Force-reloads the environment from the .env file.
    Must be called after the Setup Dialog updates user credentials.
    """
    global LLM_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY
    global MURF_API_KEY, MURF_VOICE_ID, LLM_MODEL

    # Override=True allows fresh values to replace existing environment vars
    load_dotenv(_env_path, override=True)

    # Core environment descriptors
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower().strip()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    MURF_API_KEY = os.getenv("MURF_API_KEY", "")
    MURF_VOICE_ID = os.getenv("MURF_VOICE_ID", "en-IN-isha")

    # Recalculate default models for the new provider
    LLM_MODEL = _get_default_model(LLM_PROVIDER)


def _get_default_model(provider: str) -> str:
    """
    Returns the optimized default model for the selected AI provider.
    
    Args:
        provider (str): openai, claude, or gemini.
    """
    models = {
        "openai": "gpt-4o",
        "claude": "claude-sonnet-4-20250514",
        "gemini": "gemini-2.0-flash",
    }
    return models.get(provider, "gpt-4o")


# ------------------------------------------------------------------------------
# INITIAL BOOTSTRAPPING
# ------------------------------------------------------------------------------
# We attempt to load the .env once during the module import.
if _env_path.exists():
    load_dotenv(_env_path)
else:
    # Gentle warning as the Setup Dialog will handle missing .env files later.
    print(f"[CONFIG] NOTICE: .env sequence not detected at {_env_path}.")

# ------------------------------------------------------------------------------
# APPLICATION-LEVEL CONFIGURATIONS
# ------------------------------------------------------------------------------

# Provider & API Keys
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").lower().strip()
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
MURF_API_KEY: str = os.getenv("MURF_API_KEY", "")
MURF_VOICE_ID: str = os.getenv("MURF_VOICE_ID", "en-IN-isha")

# LLM Behavior Settings (Shared across providers)
LLM_MODEL: str = _get_default_model(LLM_PROVIDER)
OPENAI_MODEL: str = "gpt-4o"  # Pre-multi-provider constant (maintained for compat)
OPENAI_MAX_TOKENS: int = 300
OPENAI_TEMPERATURE: float = 0.7
MAX_CONVERSATION_HISTORY: int = 20  # Total messages (10 turn-pairs)

# Murf TTS Fidelity Settings
MURF_MODEL_VERSION: str = "GEN2"
MURF_STYLE: str = "Conversational"
MURF_SAMPLE_RATE: int = 24000
MURF_FORMAT: str = "MP3"

# Temp File Management
AUDIO_DIR: Path = _project_root / "audio"
TEMP_AUDIO_FILE: Path = AUDIO_DIR / "temp_response.mp3"

# Human-Readable Labels for the GUI
PROVIDER_NAMES = {
    "openai": "OpenAI (GPT-4o)",
    "claude": "Claude (Anthropic)",
    "gemini": "Gemini (Google Science)",
}


def _is_placeholder(key: str) -> bool:
    """
    Checks if a credential string is a dummy value or whitespace.
    Uses common placeholder patterns from documentation.
    """
    placeholders = {"", "sk-your-key-here", "ap-your-key-here", "sk-...", "sk-...BbIA"}
    return key.strip() in placeholders


def get_active_llm_key() -> str:
    """
    Extracts the API key specific to the currently active LLM provider.
    Used for initializing AI client libraries on-demand.
    """
    keys = {
        "openai": OPENAI_API_KEY,
        "claude": ANTHROPIC_API_KEY,
        "gemini": GEMINI_API_KEY,
    }
    return keys.get(LLM_PROVIDER, "")


def has_valid_llm_key() -> bool:
    """
    Confirms if the system has a functional AI brain configured.
    Used by the main orchestrator to trigger the Setup Dialog.
    """
    key = get_active_llm_key()
    return not _is_placeholder(key)


def validate_config() -> bool:
    """
    Validates the entire configuration stack.
    
    Critical Path: An LLM key must be present.
    Warning Path: Murf key absence triggers fallback (robotic) voice.
    
    Returns:
        bool: True if critical systems are ready, False otherwise.
    """
    errors = []

    # Check the bridge to the LLM
    key = get_active_llm_key()
    if _is_placeholder(key):
        display = PROVIDER_NAMES.get(LLM_PROVIDER, LLM_PROVIDER.upper())
        errors.append(f"{display} credentials are missing or invalid.")

    # Check the bridge to premium voice
    if _is_placeholder(MURF_API_KEY):
        errors.append("MURF_API_KEY is missing. JARVIS will use offline fallback voice.")

    if errors:
        print("\n" + "=" * 60)
        print("  JARVIS — CONFIGURATION WARNING / ERROR")
        print("=" * 60)
        for err in errors:
            print(f"  X {err}")
        print("-" * 60)
        
        # If the LLM is gone, Jarvis is brainless and cannot start.
        if _is_placeholder(get_active_llm_key()):
            return False

    # Ensure the audio landing-zone exists
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    return True


def save_to_env(provider: str, api_key: str, murf_key: str = "", murf_voice: str = "") -> None:
    """
    Serializes configuration changes back to the .env file.
    This maintains persistence through reboot and ensures a sleek UX.
    
    Args:
        provider: 'openai', 'claude', or 'gemini'
        api_key: The developer key for the selected provider
        murf_key: (Optional) The Murf.ai API key
        murf_voice: (Optional) The desired Murf voice ID (e.g., en-IN-isha)
    """
    # 1. Read the current .env into memory
    current_vars = {}
    if _env_path.exists():
        with open(_env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    current_vars[k.strip()] = v.strip()

    # 2. Inject the updated configuration
    current_vars["LLM_PROVIDER"] = provider.lower().strip()

    # Determine which API key variable name should receive the new key
    key_mapping = {"openai": "OPENAI_API_KEY", "claude": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY"}
    env_target = key_mapping.get(provider.lower().strip(), "OPENAI_API_KEY")
    current_vars[env_target] = api_key.strip()

    if murf_key: current_vars["MURF_API_KEY"] = murf_key.strip()
    if murf_voice: current_vars["MURF_VOICE_ID"] = murf_voice.strip()

    # 3. Serialize back to disk with professional formatting
    header = (
        "# ============================================================\n"
        "# JARVIS — API Keys Configuration\n"
        "# ============================================================\n"
        "# DO NOT COMMIT TO PUBLIC REPOSITORIES\n"
        "# ============================================================\n\n"
    )

    with open(_env_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(f"LLM_PROVIDER={current_vars.get('LLM_PROVIDER', 'openai')}\n\n")
        f.write(f"OPENAI_API_KEY={current_vars.get('OPENAI_API_KEY', '')}\n\n")
        f.write(f"ANTHROPIC_API_KEY={current_vars.get('ANTHROPIC_API_KEY', '')}\n\n")
        f.write(f"GEMINI_API_KEY={current_vars.get('GEMINI_API_KEY', '')}\n\n")
        f.write(f"MURF_API_KEY={current_vars.get('MURF_API_KEY', '')}\n\n")
        f.write(f"MURF_VOICE_ID={current_vars.get('MURF_VOICE_ID', 'en-IN-isha')}\n")

    print(f"[CONFIG] Environment updated and serialized to disk.")


# ------------------------------------------------------------------------------
# SELF-DIAGNOSTIC (When run as a script)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print("-" * 60)
    print(" JARVIS Configuration Logic — Core Diagnostics")
    print("-" * 60)
    print(f"  Working Path  : {_project_root}")
    print(f"  Active Brain  : {LLM_PROVIDER.upper()}")
    print(f"  Brain Key Check: {'[VALID]' if has_valid_llm_key() else '[MISSING]'}")
    print(f"  Murf Key Check: {'[VALID]' if not _is_placeholder(MURF_API_KEY) else '[MISSING]'}")
    print("-" * 60)
    
    if validate_config():
        print("  STATUS: SYSTEM READY. Launch main.py to begin.")
    else:
        print("  STATUS: CRITICAL FAILURE. Use --setup to resolve.")
        sys.exit(1)
