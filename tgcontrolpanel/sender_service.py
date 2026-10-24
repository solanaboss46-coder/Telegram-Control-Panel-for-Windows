"""Message sender service: scheduled sending to multiple recipients."""
from __future__ import annotations

import asyncio
import threading

from .db import Database


class SenderService:
    def __init__(self, db: Database, client_manager) -> None:
        self.db = db
        self.cm = client_manager
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def send_batch(
        self,
        account_id: int,
        recipients: list[int],
        text: str,
        interval: float,
        preview_only: bool = False,
    ) -> None:
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run_batch,
            args=(account_id, recipients, text, interval, preview_only),
            name="sender",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run_batch(self, account_id, recipients, text, interval, preview_only) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._batch(account_id, recipients, text, interval, preview_only))
        finally:
            loop.close()

    async def _batch(self, account_id, recipients, text, interval, preview_only) -> None:
        client = self.cm.get_client(account_id)
        if not client:
            self.cm.error.emit(account_id, "Account not connected")
            return
        for chat_id in recipients:
            if self._stop.is_set():
                break
            if preview_only:
                self.cm.new_message.emit(
                    account_id,
                    {"id": 0, "text": f"[PREVIEW] {text}", "chat_id": chat_id, "out": True, "status": "preview"},
                )
                continue
            try:
                sent = await client.send_message(chat_id, text)
                self.cm.new_message.emit(
                    account_id,
                    {
                        "id": sent.id,
                        "text": text,
                        "date": sent.date.isoformat() if sent.date else "",
                        "chat_id": chat_id,
                        "out": True,
                        "status": "sent",
                    },
                )
                self.db.add_event("send_message", message=f"Sent to {chat_id}", account_id=account_id)
            except Exception as exc:  # noqa: BLE001
                self.cm.error.emit(account_id, f"Send to {chat_id} failed: {exc}")
                self.db.add_event("send_error", message=f"Send to {chat_id} failed: {exc}", account_id=account_id)
            if interval > 0 and not self._stop.is_set():
                await asyncio.sleep(interval)
