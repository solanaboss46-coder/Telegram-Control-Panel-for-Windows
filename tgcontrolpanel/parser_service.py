"""Member parser service."""
from __future__ import annotations

import csv
from typing import Any

from .config import EXPORT_DIR
from .db import Database


class ParserService:
    def __init__(self, db: Database, client_manager) -> None:
        self.db = db
        self.cm = client_manager
        self._stop = False

    def load_participants(self, account_id: int, chat_id: int) -> None:
        self.cm.load_participants(account_id, chat_id)

    def export_csv(self, participants: list[dict[str, Any]], filename: str | None = None) -> str:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        if not filename:
            filename = "participants.csv"
        path = EXPORT_DIR / filename
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "username", "name", "phone", "bot"])
            writer.writeheader()
            for p in participants:
                writer.writerow(
                    {
                        "id": p.get("id", ""),
                        "username": p.get("username", ""),
                        "name": p.get("name", ""),
                        "phone": p.get("phone", ""),
                        "bot": p.get("bot", False),
                    }
                )
        return str(path)

    def stop(self) -> None:
        self._stop = True
