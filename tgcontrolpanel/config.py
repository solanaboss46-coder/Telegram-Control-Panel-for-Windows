"""Application configuration and path constants."""
from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "tgcontrolpanel"
APP_DISPLAY_NAME = "Telegram Control Panel"

# Base data directory: %APPDATA%/tgcontrolpanel on Windows, ~/.local/share/tgcontrolpanel on Linux.
if os.name == "nt":
    BASE_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
else:
    BASE_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_NAME

DATA_DIR = BASE_DIR
SESSIONS_DIR = BASE_DIR / "sessions"
LOGS_DIR = BASE_DIR / "logs"
EXPORT_DIR = BASE_DIR / "exports"

DB_PATH = BASE_DIR / "app.db"
KEY_PATH = BASE_DIR / "key.bin"
SETTINGS_FILE = BASE_DIR / "settings.json"

# Default Telegram API values (placeholders; user must supply their own from my.telegram.org).
DEFAULT_API_ID = ""
DEFAULT_API_HASH = ""

# Update poll interval for inbox (seconds).
INBOX_POLL_INTERVAL = 5.0

# Connection timeouts (seconds).
CONNECT_TIMEOUT = 30
DISCONNECT_TIMEOUT = 10

__all__ = [
    "APP_DISPLAY_NAME",
    "APP_NAME",
    "BASE_DIR",
    "CONNECT_TIMEOUT",
    "DATA_DIR",
    "DB_PATH",
    "DEFAULT_API_HASH",
    "DEFAULT_API_ID",
    "DISCONNECT_TIMEOUT",
    "EXPORT_DIR",
    "INBOX_POLL_INTERVAL",
    "KEY_PATH",
    "LOGS_DIR",
    "SESSIONS_DIR",
    "SETTINGS_FILE",
]
