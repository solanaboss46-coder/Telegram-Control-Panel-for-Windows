# Telegram Control Panel for Windows

Desktop application for managing multiple Telegram accounts through a single GUI.

## Requirements

- Python 3.10+
- PySide6, Telethon, cryptography

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python -m tgcontrolpanel
```

## Building the Windows `.exe`

On Windows, use PyInstaller:

```bash
pip install pyinstaller
pyinstaller --noconsole --name "Telegram Control Panel" tgcontrolpanel/main.py
```

The produced `dist/Telegram Control Panel.exe` is a standalone Windows executable. Data (sessions, DB, settings) is stored under `%APPDATA%/tgcontrolpanel`.

## Features

- Dashboard with account/proxy/message counters and recent events
- Account manager: add (API ID/Hash + phone), connect/disconnect, rename, delete, session storage
- Proxy manager: socks5/socks4/http, connection test, assign proxy to account
- Inbox: per-account dialogs, message history, send/reply, unread highlighting, search, all-accounts mode
- Member parser: load chat participants, search/filter, CSV export
- Message sender: recipients, interval, preview, start/stop, result log
- Event log with filters (account, type, time)
- Settings: API defaults, poll interval

## Security

API ID/Hash and proxy passwords are encrypted at rest (Fernet) under the app data directory. Logs never record passwords, login codes, or full session data.

## Notes

- You must provide your own `api_id`/`api_hash` from https://my.telegram.org.
- Authorization uses the standard Telegram login code flow (plus 2FA when enabled).
- No automatic proxy rotation or mass messaging to strangers is implemented, per the specification.
