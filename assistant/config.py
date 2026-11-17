"""Settings, read from environment variables or a .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("ASSISTANT_MODEL", "claude-opus-5-5")
EFFORT = os.getenv("ASSISTANT_EFFORT", "medium")  # low | medium | high

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))

DATA_DIR = Path(os.getenv("ASSISTANT_DATA_DIR") or Path.home() / ".daily-assistant").expanduser()
DATA_FILE = DATA_DIR / "data.json"


def email_configured() -> bool:
    return bool(EMAIL_ADDRESS and EMAIL_PASSWORD)
