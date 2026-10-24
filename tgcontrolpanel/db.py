"""Local SQLite storage for accounts, proxies, settings, and events."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import DB_PATH


def _now() -> str:
    return datetime.now(UTC).isoformat()


class Database:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            PRAGMA journal_mode=WAL;

            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                api_id TEXT,
                api_hash TEXT,
                session_file TEXT,
                status TEXT DEFAULT 'disconnected',
                last_check TEXT,
                error_message TEXT,
                proxy_id INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (proxy_id) REFERENCES proxies(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                username TEXT,
                password TEXT,
                status TEXT DEFAULT 'unknown',
                last_check TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                account_id INTEGER,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_events_account ON events(account_id);
            """
        )
        self.conn.commit()

    @contextmanager
    def transaction(self):
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    # ---------------- accounts ----------------
    def add_account(
        self,
        name: str,
        phone: str | None,
        api_id: str | None,
        api_hash: str | None,
        session_file: str | None,
        proxy_id: int | None = None,
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO accounts (name, phone, api_id, api_hash, session_file, proxy_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, phone, api_id, api_hash, session_file, proxy_id),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_accounts(self) -> list[dict[str, Any]]:
        cur = self.conn.execute(
            """
            SELECT a.*, p.name AS proxy_name, p.type AS proxy_type
            FROM accounts a
            LEFT JOIN proxies p ON a.proxy_id = p.id
            ORDER BY a.id
            """
        )
        return [dict(r) for r in cur.fetchall()]

    def get_account(self, account_id: int) -> dict[str, Any] | None:
        cur = self.conn.execute(
            """
            SELECT a.*, p.name AS proxy_name, p.type AS proxy_type
            FROM accounts a
            LEFT JOIN proxies p ON a.proxy_id = p.id
            WHERE a.id = ?
            """,
            (account_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def update_account(
        self,
        account_id: int,
        **fields: Any,
    ) -> None:
        if not fields:
            return
        cols = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [account_id]
        self.conn.execute(f"UPDATE accounts SET {cols} WHERE id = ?", values)
        self.conn.commit()

    def delete_account(self, account_id: int) -> None:
        self.conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        self.conn.commit()

    def set_account_status(
        self,
        account_id: int,
        status: str,
        error_message: str | None = None,
        last_check: str | None = None,
    ) -> None:
        fields: dict[str, Any] = {"status": status}
        if error_message is not None:
            fields["error_message"] = error_message
        if last_check is not None:
            fields["last_check"] = last_check
        self.update_account(account_id, **fields)

    # ---------------- proxies ----------------
    def add_proxy(
        self,
        name: str,
        type: str,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO proxies (name, type, host, port, username, password)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, type, host, port, username, password),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_proxies(self) -> list[dict[str, Any]]:
        cur = self.conn.execute("SELECT * FROM proxies ORDER BY id")
        return [dict(r) for r in cur.fetchall()]

    def get_proxy(self, proxy_id: int) -> dict[str, Any] | None:
        cur = self.conn.execute("SELECT * FROM proxies WHERE id = ?", (proxy_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def update_proxy(self, proxy_id: int, **fields: Any) -> None:
        if not fields:
            return
        cols = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [proxy_id]
        self.conn.execute(f"UPDATE proxies SET {cols} WHERE id = ?", values)
        self.conn.commit()

    def delete_proxy(self, proxy_id: int) -> None:
        self.conn.execute("UPDATE accounts SET proxy_id = NULL WHERE proxy_id = ?", (proxy_id,))
        self.conn.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
        self.conn.commit()

    def set_proxy_status(
        self,
        proxy_id: int,
        status: str,
        error_message: str | None = None,
        last_check: str | None = None,
    ) -> None:
        fields: dict[str, Any] = {"status": status}
        if error_message is not None:
            fields["error_message"] = error_message
        if last_check is not None:
            fields["last_check"] = last_check
        self.update_proxy(proxy_id, **fields)

    # ---------------- settings ----------------
    def get_setting(self, key: str, default: Any = None) -> Any:
        cur = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        if row is None:
            return default
        try:
            return json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            return row["value"]

    def set_setting(self, key: str, value: Any) -> None:
        self.conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, json.dumps(value, ensure_ascii=False)),
        )
        self.conn.commit()

    # ---------------- events ----------------
    def add_event(
        self,
        type: str,
        message: str,
        account_id: int | None = None,
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO events (timestamp, account_id, type, message)
            VALUES (?, ?, ?, ?)
            """,
            (_now(), account_id, type, message),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_events(
        self,
        account_id: int | None = None,
        type: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM events"
        params: list[Any] = []
        conditions = []
        if account_id is not None:
            conditions.append("account_id = ?")
            params.append(account_id)
        if type is not None:
            conditions.append("type = ?")
            params.append(type)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        cur = self.conn.execute(query, params)
        return [dict(r) for r in cur.fetchall()]

    def clear_events(self) -> None:
        self.conn.execute("DELETE FROM events")
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
