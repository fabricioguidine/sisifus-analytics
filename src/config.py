"""Configuration settings for the application"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Email storage file in input folder
EMAILS_STORAGE_FILE = INPUT_DIR / "emails.json"

# Email configuration
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "gmail")  # gmail, outlook, imap
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")  # Use app-specific password
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))

# Security: Use app-specific passwords for Gmail
# Never commit .env file with real credentials

# Analytics output files
ANALYTICS_JSON = OUTPUT_DIR / "analytics.json"
ANALYTICS_CSV = OUTPUT_DIR / "applications.csv"
SANKEY_HTML = OUTPUT_DIR / "sankey_diagram.html"


def enable_utf8_stdout() -> None:
    """Best-effort: force UTF-8 on stdout/stderr so glyphs print on Windows cp1252 consoles."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass
