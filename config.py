# ============================================================
# JARVIS — Configuration Loader
# ============================================================
# Loads API keys and settings from .env file.
# Validates that all required keys are present at startup.
# ============================================================

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from the project root ──────────────────────────
_project_root = Path(__file__).resolve().parent
_env_path = _project_root / ".env"

if _env_path.exists():
    load_dotenv(_env_path)
else:
    print(f"[CONFIG] WARNING: .env file not found at {_env_path}")
    print("[CONFIG] Create a .env file with your API keys. See README.md for details.")

# ── API Keys ─────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
MURF_API_KEY: str = os.getenv("MURF_API_KEY", "")
MURF_VOICE_ID: str = os.getenv("MURF_VOICE_ID", "en-IN-isha")

# ── Settings ─────────────────────────────────────────────────
MURF_MODEL_VERSION: str = "GEN2"          # Falcon model
MURF_STYLE: str = "Conversational"
MURF_SAMPLE_RATE: int = 24000
MURF_FORMAT: str = "MP3"

OPENAI_MODEL: str = "gpt-4o"
OPENAI_MAX_TOKENS: int = 300
OPENAI_TEMPERATURE: float = 0.7

MAX_CONVERSATION_HISTORY: int = 20        # Keep last 20 messages (10 exchanges)

# Audio temp file path
AUDIO_DIR: Path = _project_root / "audio"
TEMP_AUDIO_FILE: Path = AUDIO_DIR / "temp_response.mp3"


def validate_config() -> bool:
    """
    Validates that all required API keys are set.
    Returns True if valid, prints errors and returns False otherwise.
    """
    errors = []

    if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-your-key-here":
        errors.append(
            "OPENAI_API_KEY is not set. Get yours at https://platform.openai.com/api-keys"
        )

    if not MURF_API_KEY or MURF_API_KEY == "ap-your-key-here":
        errors.append(
            "MURF_API_KEY is not set. Get yours at https://murf.ai/resources/api"
        )

    if errors:
        print("\n" + "=" * 60)
        print("  JARVIS — CONFIGURATION ERROR")
        print("=" * 60)
        for err in errors:
            print(f"  ✗ {err}")
        print()
        print("  Fix: Open the .env file in the project root and add your keys.")
        print("=" * 60 + "\n")
        return False

    # Ensure audio directory exists
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    return True


# ── Quick self-test when run directly ────────────────────────
if __name__ == "__main__":
    print("[CONFIG] Testing configuration loader...")
    print(f"  Project Root  : {_project_root}")
    print(f"  .env Path     : {_env_path} ({'EXISTS' if _env_path.exists() else 'MISSING'})")
    print(f"  OpenAI Key    : {'SET' if OPENAI_API_KEY and OPENAI_API_KEY != 'sk-your-key-here' else 'NOT SET'}")
    print(f"  Murf Key      : {'SET' if MURF_API_KEY and MURF_API_KEY != 'ap-your-key-here' else 'NOT SET'}")
    print(f"  Murf Voice    : {MURF_VOICE_ID}")
    print(f"  OpenAI Model  : {OPENAI_MODEL}")
    print(f"  Audio Dir     : {AUDIO_DIR}")

    if validate_config():
        print("\n  ✓ Configuration is valid. Ready to launch JARVIS.")
    else:
        print("\n  ✗ Configuration has errors. Fix them before running.")
        sys.exit(1)
