# Agent instructions (Kilo)

Project: Telegram Control Panel for Windows (Python + PySide6 + Telethon).

## Commands

- Create/activate venv: `python3 -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run app: `QT_QPA_PLATFORM=offscreen python -m tgcontrolpanel` (headless) or `python -m tgcontrolpanel`
- Lint: `ruff check tgcontrolpanel/`
- Entrypoint: `tgcontrolpanel/main.py`
- Package: `tgcontrolpanel/`

## Notes

- DB path: `tgcontrolpanel/config.py` (`BASE_DIR` / `app.db`)
- Sessions stored under `SESSIONS_DIR` (`sessions/`)
- Sensitive fields encrypted via `tgcontrolpanel/crypto.py` (Fernet)
- GUI pages under `tgcontrolpanel/gui/`
- Services under `tgcontrolpanel/*.py` (`account_service`, `proxy_service`, `inbox_service`, `parser_service`, `sender_service`)
- `ClientManager` runs Telethon on a background asyncio thread and bridges events to Qt signals.
