# ============================================================
# JARVIS — Configuration Loader
# ============================================================
# Loads API keys and settings from .env file.
# Supports multiple LLM providers: OpenAI, Claude, Gemini.
# Validates that the selected provider's key is present.
# ============================================================

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from the project root ──────────────────────────
_project_root = Path(__file__).resolve().parent
_env_path = _project_root / ".env"


def reload_env():
    """
    Re-reads the .env file and refreshes all module-level config vars.
    Call this after the setup dialog writes new keys to .env.
    """
    global LLM_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY
    global MURF_API_KEY, MURF_VOICE_ID, OPENAI_MODEL, LLM_MODEL

    load_dotenv(_env_path, override=True)

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower().strip()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    MURF_API_KEY = os.getenv("MURF_API_KEY", "")
    MURF_VOICE_ID = os.getenv("MURF_VOICE_ID", "en-IN-isha")

    # Set the active model based on provider
    LLM_MODEL = _get_default_model(LLM_PROVIDER)


def _get_default_model(provider: str) -> str:
    """Returns the default model name for the given provider."""
    models = {
        "openai": "gpt-4o",
        "claude": "claude-sonnet-4-20250514",
        "gemini": "gemini-2.0-flash",
    }
    return models.get(provider, "gpt-4o")


# ── Initial load ─────────────────────────────────────────────
if _env_path.exists():
    load_dotenv(_env_path)
else:
    print(f"[CONFIG] WARNING: .env file not found at {_env_path}")
    print("[CONFIG] Create a .env file with your API keys. See README.md for details.")

# ── LLM Provider Selection ──────────────────────────────────
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").lower().strip()

# ── API Keys ─────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
MURF_API_KEY: str = os.getenv("MURF_API_KEY", "")
MURF_VOICE_ID: str = os.getenv("MURF_VOICE_ID", "en-IN-isha")

# ── LLM Settings ────────────────────────────────────────────
LLM_MODEL: str = _get_default_model(LLM_PROVIDER)
OPENAI_MODEL: str = "gpt-4o"                  # kept for backward compat
OPENAI_MAX_TOKENS: int = 300
OPENAI_TEMPERATURE: float = 0.7

MAX_CONVERSATION_HISTORY: int = 20             # Keep last 20 messages

# ── Murf TTS Settings ───────────────────────────────────────
MURF_MODEL_VERSION: str = "GEN2"
MURF_STYLE: str = "Conversational"
MURF_SAMPLE_RATE: int = 24000
MURF_FORMAT: str = "MP3"

# ── Audio Paths ──────────────────────────────────────────────
AUDIO_DIR: Path = _project_root / "audio"
TEMP_AUDIO_FILE: Path = AUDIO_DIR / "temp_response.mp3"

# ── Provider display names ───────────────────────────────────
PROVIDER_NAMES = {
    "openai": "OpenAI (GPT-4o)",
    "claude": "Claude (Anthropic)",
    "gemini": "Gemini (Google)",
}


def _is_placeholder(key: str) -> bool:
    """Check if an API key is a placeholder / empty."""
    placeholders = {"", "sk-your-key-here", "ap-your-key-here",
                    "sk-...", "sk-...BbIA"}
    return key.strip() in placeholders


def get_active_llm_key() -> str:
    """Returns the API key for the currently selected LLM provider."""
    keys = {
        "openai": OPENAI_API_KEY,
        "claude": ANTHROPIC_API_KEY,
        "gemini": GEMINI_API_KEY,
    }
    return keys.get(LLM_PROVIDER, "")


def has_valid_llm_key() -> bool:
    """
    Returns True if the selected LLM provider has a non-placeholder key set.
    Used to decide whether to show the setup dialog.
    """
    key = get_active_llm_key()
    return not _is_placeholder(key)


def validate_config() -> bool:
    """
    Validates that the selected LLM provider's key and Murf key are set.
    Returns True if valid, prints errors and returns False otherwise.
    """
    errors = []

    # Validate the active LLM provider's key
    key = get_active_llm_key()
    if _is_placeholder(key):
        provider_name = PROVIDER_NAMES.get(LLM_PROVIDER, LLM_PROVIDER)
        errors.append(
            f"{provider_name} API key is not set. "
            f"Run JARVIS again or use --setup to configure it."
        )

    if not MURF_API_KEY or MURF_API_KEY == "ap-your-key-here":
        errors.append(
            "MURF_API_KEY is not set. Get yours at https://murf.ai/resources/api\n"
            "         (TTS will fall back to offline pyttsx3 voice)"
        )

    if errors:
        print("\n" + "=" * 60)
        print("  JARVIS — CONFIGURATION ERROR")
        print("=" * 60)
        for err in errors:
            print(f"  ✗ {err}")
        print()
        print("  Fix: Run with --setup or edit .env in the project root.")
        print("=" * 60 + "\n")
        # Only the LLM key is truly critical
        if _is_placeholder(get_active_llm_key()):
            return False

    # Ensure audio directory exists
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    return True


def save_to_env(provider: str, api_key: str, murf_key: str = "",
                murf_voice: str = "") -> None:
    """
    Writes/updates the .env file with the given provider and keys.
    Preserves any existing keys not being changed.
    """
    # Read existing .env content (if any)
    existing = {}
    if _env_path.exists():
        with open(_env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    existing[k.strip()] = v.strip()

    # Update with new values
    existing["LLM_PROVIDER"] = provider.lower().strip()

    # Set the key for the selected provider
    key_map = {
        "openai": "OPENAI_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }
    env_key_name = key_map.get(provider.lower().strip(), "OPENAI_API_KEY")
    existing[env_key_name] = api_key.strip()

    if murf_key:
        existing["MURF_API_KEY"] = murf_key.strip()
    if murf_voice:
        existing["MURF_VOICE_ID"] = murf_voice.strip()

    # Write the .env file with nice comments
    with open(_env_path, "w", encoding="utf-8") as f:
        f.write("# ============================================================\n")
        f.write("# JARVIS — API Keys Configuration\n")
        f.write("# ============================================================\n")
        f.write("# Auto-generated by JARVIS setup. NEVER commit to GitHub!\n")
        f.write("# ============================================================\n\n")

        f.write(f"# LLM Provider: openai, claude, or gemini\n")
        f.write(f"LLM_PROVIDER={existing.get('LLM_PROVIDER', 'openai')}\n\n")

        f.write(f"# OpenAI GPT-4o API Key\n")
        f.write(f"OPENAI_API_KEY={existing.get('OPENAI_API_KEY', '')}\n\n")

        f.write(f"# Anthropic Claude API Key\n")
        f.write(f"ANTHROPIC_API_KEY={existing.get('ANTHROPIC_API_KEY', '')}\n\n")

        f.write(f"# Google Gemini API Key\n")
        f.write(f"GEMINI_API_KEY={existing.get('GEMINI_API_KEY', '')}\n\n")

        f.write(f"# Murf AI Text-to-Speech API Key\n")
        f.write(f"MURF_API_KEY={existing.get('MURF_API_KEY', '')}\n\n")

        f.write(f"# Murf Voice ID\n")
        f.write(f"MURF_VOICE_ID={existing.get('MURF_VOICE_ID', 'en-IN-isha')}\n")

    print(f"[CONFIG] Saved configuration to {_env_path}")


# ── Quick self-test when run directly ────────────────────────
if __name__ == "__main__":
    print("[CONFIG] Testing configuration loader...")
    print(f"  Project Root  : {_project_root}")
    print(f"  .env Path     : {_env_path} ({'EXISTS' if _env_path.exists() else 'MISSING'})")
    print(f"  LLM Provider  : {LLM_PROVIDER}")
    print(f"  LLM Model     : {LLM_MODEL}")
    print(f"  OpenAI Key    : {'SET' if not _is_placeholder(OPENAI_API_KEY) else 'NOT SET'}")
    print(f"  Claude Key    : {'SET' if not _is_placeholder(ANTHROPIC_API_KEY) else 'NOT SET'}")
    print(f"  Gemini Key    : {'SET' if not _is_placeholder(GEMINI_API_KEY) else 'NOT SET'}")
    print(f"  Murf Key      : {'SET' if MURF_API_KEY and MURF_API_KEY != 'ap-your-key-here' else 'NOT SET'}")
    print(f"  Murf Voice    : {MURF_VOICE_ID}")
    print(f"  Audio Dir     : {AUDIO_DIR}")

    if validate_config():
        print("\n  ✓ Configuration is valid. Ready to launch JARVIS.")
    else:
        print("\n  ✗ Configuration has errors. Fix them before running.")
        sys.exit(1)
