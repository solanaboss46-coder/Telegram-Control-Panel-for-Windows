"""Telethon client wrapper managing multiple accounts on a background asyncio loop."""
from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from datetime import UTC

from PySide6.QtCore import QObject, Signal
from telethon import TelegramClient, events
from telethon.errors import (
    FloodWaitError,
    SessionPasswordNeededError,
)

from .config import CONNECT_TIMEOUT, DISCONNECT_TIMEOUT, SESSIONS_DIR
from .crypto import decrypt
from .db import Database

SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class AccountData:
    id: int
    name: str
    phone: str | None
    api_id: str | None
    api_hash: str | None
    session_file: str | None
    proxy: dict | None = None


class ClientManager(QObject):
    """Bridge between Telethon async clients and the PySide GUI."""

    connected = Signal(int, str)            # account_id, name
    disconnected = Signal(int)              # account_id
    authorization_required = Signal(int, str)  # account_id, phone
    twofa_required = Signal(int)            # account_id
    code_sent = Signal(int)                 # account_id
    error = Signal(int, str)                # account_id, message
    new_message = Signal(int, dict)         # account_id, message dict
    dialogs_loaded = Signal(int, list)      # account_id, list of dialog dicts
    participants_loaded = Signal(int, list) # account_id, list of participant dicts
    operation_log = Signal(str)             # generic log line

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._clients: dict[int, TelegramClient] = {}
        self._code_futures: dict[int, asyncio.Future] = {}
        self._lock = threading.Lock()

    # ---------------- lifecycle ----------------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, name="tg-loop", daemon=True)
        self._thread.start()

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        finally:
            self._loop.close()
            self._loop = None

    def _coro(self, coro):
        if self._loop is None:
            raise RuntimeError("client loop not started")
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def stop(self) -> None:
        self._stop.set()
        for account_id in list(self._clients.keys()):
            self.disconnect_account(account_id)
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=DISCONNECT_TIMEOUT)

    # ---------------- account lifecycle ----------------
    def connect_account(self, account_id: int) -> None:
        row = self.db.get_account(account_id)
        if not row:
            self.error.emit(account_id, "Account not found")
            return
        acc = AccountData(
            id=row["id"],
            name=row["name"],
            phone=row["phone"],
            api_id=decrypt(row["api_id"]) if row["api_id"] else None,
            api_hash=decrypt(row["api_hash"]) if row["api_hash"] else None,
            session_file=row["session_file"],
            proxy=row if row["proxy_id"] else None,
        )
        self._coro(self._connect(acc))

    async def _connect(self, acc: AccountData) -> None:
        try:
            client = TelegramClient(
                acc.session_file or str(SESSIONS_DIR / f"{acc.id}.session"),
                int(acc.api_id) if acc.api_id else 0,
                acc.api_hash or "",
                proxy=self._build_proxy(acc.proxy) if acc.proxy else None,
                timeout=CONNECT_TIMEOUT,
            )
            self._clients[acc.id] = client
            await client.connect()

            if await client.is_user_authorized():
                me = await client.get_me()
                self.db.set_account_status(acc.id, "connected", last_check=_iso_now())
                self._register_handlers(acc.id, client)
                self.connected.emit(acc.id, me.username or me.first_name or acc.name or str(acc.id))
                self.operation_log.emit(f"Connected: {acc.name}")
            else:
                self.db.set_account_status(acc.id, "authorization_required")
                self.authorization_required.emit(acc.id, acc.phone or "")
                code = await self._wait_code(acc.id)
                if isinstance(code, tuple) and code[0] == "cancel":
                    return
                try:
                    await client.sign_in(acc.phone, code)
                except SessionPasswordNeededError:
                    self.db.set_account_status(acc.id, "authorization_required")
                    self.twofa_required.emit(acc.id)
                    pw = await self._wait_code(acc.id)
                    if isinstance(pw, tuple) and pw[0] == "cancel":
                        return
                    await client.sign_in(password=pw[1])
                me = await client.get_me()
                self.db.set_account_status(acc.id, "connected", last_check=_iso_now())
                self._register_handlers(acc.id, client)
                self.connected.emit(acc.id, me.username or me.first_name or acc.name or str(acc.id))
                self.operation_log.emit(f"Connected: {acc.name}")
                self.code_sent.emit(acc.id)
        except Exception as exc:  # noqa: BLE001
            self.db.set_account_status(acc.id, "error", error_message=str(exc))
            self.error.emit(acc.id, str(exc))
            self.operation_log.emit(f"Connect error {acc.name}: {exc}")

    async def _wait_code(self, account_id: int):
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self._code_futures[account_id] = fut
        try:
            return await fut
        finally:
            self._code_futures.pop(account_id, None)

    def disconnect_account(self, account_id: int) -> None:
        self._coro(self._disconnect(account_id))

    async def _disconnect(self, account_id: int) -> None:
        client = self._clients.pop(account_id, None)
        if client:
            try:
                await client.disconnect()
            except Exception as exc:  # noqa: BLE001
                self.operation_log.emit(f"Disconnect error {account_id}: {exc}")
        self.db.set_account_status(account_id, "disconnected")
        self.disconnected.emit(account_id)

    def submit_code(self, account_id: int, code: str) -> None:
        fut = self._code_futures.get(account_id)
        if fut and not fut.done():
            fut.set_result(code)

    def submit_password(self, account_id: int, password: str) -> None:
        fut = self._code_futures.get(account_id)
        if fut and not fut.done():
            fut.set_result(("2fa", password))

    def get_client(self, account_id: int):
        with self._lock:
            return self._clients.get(account_id)

    # ---------------- helpers ----------------
    def _build_proxy(self, proxy: dict) -> dict | None:
        ptype = (proxy.get("type") or "").lower()
        host = proxy.get("host")
        port = int(proxy["port"]) if proxy.get("port") else None
        username = proxy.get("username")
        password = decrypt(proxy["password"]) if proxy.get("password") else None
        if not host or not port:
            return None
        if ptype in ("socks5", "socks4"):
            return (ptype, host, port, username, password)
        if ptype == "http":
            return ("http", host, port, username, password)
        return None

    def _register_handlers(self, account_id: int, client: TelegramClient) -> None:
        @client.on(events.NewMessage)
        async def handler(event):
            try:
                msg = await self._message_to_dict(event, client)
                self.new_message.emit(account_id, msg)
                self.db.add_event("new_message", message=f"New message in chat {msg.get('chat_id')}", account_id=account_id)
            except Exception:  # noqa: BLE001, S110
                pass

    async def _message_to_dict(self, event, client) -> dict:
        sender = await event.get_sender()
        chat = await event.get_chat()
        return {
            "id": event.id,
            "text": event.message.text or "",
            "date": event.message.date.isoformat() if event.message.date else "",
            "sender_id": sender.id if sender else None,
            "sender_name": self._display_name(sender) if sender else "",
            "chat_id": chat.id if chat else None,
            "chat_title": getattr(chat, "title", None) or self._display_name(chat) if chat else "",
            "out": bool(event.message.out),
            "unread": not bool(event.message.out),
        }

    @staticmethod
    def _display_name(entity) -> str:
        if entity is None:
            return ""
        parts = []
        if getattr(entity, "first_name", None):
            parts.append(entity.first_name)
        if getattr(entity, "last_name", None):
            parts.append(entity.last_name)
        if parts:
            return " ".join(parts)
        return getattr(entity, "username", None) or getattr(entity, "title", None) or str(entity.id)

    # ---------------- operations ----------------
    def load_dialogs(self, account_id: int, limit: int = 50) -> None:
        self._coro(self._load_dialogs(account_id, limit))

    async def _load_dialogs(self, account_id: int, limit: int) -> None:
        client = self._clients.get(account_id)
        if not client:
            self.error.emit(account_id, "Not connected")
            return
        dialogs = []
        async for dialog in client.iter_dialogs(limit=limit):
            entity = dialog.entity
            dialogs.append(
                {
                    "id": dialog.id,
                    "title": dialog.title or self._display_name(entity) or str(dialog.id),
                    "chat_id": entity.id if entity else dialog.id,
                    "unread_count": dialog.unread_count,
                    "is_channel": getattr(entity, "broadcast", False),
                    "is_group": getattr(entity, "megagroup", False),
                    "date": dialog.date.isoformat() if dialog.date else "",
                }
            )
        self.dialogs_loaded.emit(account_id, dialogs)

    def load_messages(self, account_id: int, chat_id: int, limit: int = 100) -> None:
        self._coro(self._load_messages(account_id, chat_id, limit))

    async def _load_messages(self, account_id: int, chat_id: int, limit: int) -> None:
        client = self._clients.get(account_id)
        if not client:
            self.error.emit(account_id, "Not connected")
            return
        messages = []
        async for message in client.iter_messages(chat_id, limit=limit):
            sender = await message.get_sender()
            messages.append(
                {
                    "id": message.id,
                    "text": message.text or "",
                    "date": message.date.isoformat() if message.date else "",
                    "sender_id": sender.id if sender else None,
                    "sender_name": self._display_name(sender) if sender else "",
                    "out": bool(message.out),
                    "unread": not bool(message.out),
                }
            )
        self.new_message.emit(account_id, {"__batch__": True, "chat_id": chat_id, "messages": messages})

    def send_message(self, account_id: int, chat_id: int, text: str) -> None:
        self._coro(self._send_message(account_id, chat_id, text))

    async def _send_message(self, account_id: int, chat_id: int, text: str) -> None:
        client = self._clients.get(account_id)
        if not client:
            self.error.emit(account_id, "Not connected")
            return
        try:
            sent = await client.send_message(chat_id, text)
            self.db.add_event("send_message", message=f"Sent to chat {chat_id}", account_id=account_id)
            self.new_message.emit(
                account_id,
                {
                    "id": sent.id,
                    "text": text,
                    "date": sent.date.isoformat() if sent.date else "",
                    "sender_id": (await client.get_me()).id,
                    "sender_name": "me",
                    "chat_id": chat_id,
                    "out": True,
                    "unread": False,
                    "status": "sent",
                },
            )
        except FloodWaitError as exc:
            self.error.emit(account_id, f"Flood wait: {exc.seconds}s")
        except Exception as exc:  # noqa: BLE001
            self.error.emit(account_id, str(exc))

    def load_participants(self, account_id: int, chat_id: int) -> None:
        self._coro(self._load_participants(account_id, chat_id))

    async def _load_participants(self, account_id: int, chat_id: int) -> None:
        client = self._clients.get(account_id)
        if not client:
            self.error.emit(account_id, "Not connected")
            return
        participants = []
        seen = set()
        try:
            async for user in client.iter_participants(chat_id):
                if user.id in seen:
                    continue
                seen.add(user.id)
                participants.append(
                    {
                        "id": user.id,
                        "username": user.username or "",
                        "name": self._display_name(user),
                        "phone": user.phone or "",
                        "bot": bool(user.bot),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            self.error.emit(account_id, f"Participants error: {exc}")
        self.participants_loaded.emit(account_id, participants)

    def check_connection(self, account_id: int) -> None:
        self._coro(self._check_connection(account_id))

    async def _check_connection(self, account_id: int) -> None:
        client = self._clients.get(account_id)
        if not client:
            self.error.emit(account_id, "Not connected")
            return
        try:
            await client.get_me()
            self.db.set_account_status(account_id, "connected", last_check=_iso_now())
        except Exception as exc:  # noqa: BLE001
            self.db.set_account_status(account_id, "error", error_message=str(exc))
            self.error.emit(account_id, str(exc))


def _iso_now() -> str:
    from datetime import datetime

    return datetime.now(UTC).isoformat()
