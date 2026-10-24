"""Inbox service: dialogs and messages per account."""
from __future__ import annotations

from typing import Any

from .db import Database


class InboxService:
    def __init__(self, db: Database, client_manager) -> None:
        self.db = db
        self.cm = client_manager

    def load_dialogs(self, account_id: int, limit: int = 50) -> None:
        self.cm.load_dialogs(account_id, limit)

    def load_messages(self, account_id: int, chat_id: int, limit: int = 100) -> None:
        self.cm.load_messages(account_id, chat_id, limit)

    def send_message(self, account_id: int, chat_id: int, text: str) -> None:
        self.cm.send_message(account_id, chat_id, text)
        self.db.add_event(
            "send_message",
            message=f"Sent message to chat {chat_id}",
            account_id=account_id,
        )

    def get_recent_events(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.db.get_events(limit=limit)
