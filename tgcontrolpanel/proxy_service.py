"""Proxy service: CRUD and connection checking."""
from __future__ import annotations

from datetime import UTC
from typing import Any

from .crypto import decrypt, encrypt
from .db import Database


class ProxyService:
    def __init__(self, db: Database, client_manager) -> None:
        self.db = db
        self.cm = client_manager

    def list_proxies(self) -> list[dict[str, Any]]:
        proxies = self.db.get_proxies()
        for p in proxies:
            p["password"] = decrypt(p.get("password") or "")
        return proxies

    def add_proxy(
        self,
        name: str,
        type: str,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
    ) -> int:
        return self.db.add_proxy(
            name=name,
            type=type,
            host=host,
            port=port,
            username=username,
            password=encrypt(password) if password else None,
        )

    def get_proxy(self, proxy_id: int) -> dict[str, Any] | None:
        p = self.db.get_proxy(proxy_id)
        if p:
            p["password"] = decrypt(p.get("password") or "")
        return p

    def update_proxy(self, proxy_id: int, **fields: Any) -> None:
        if fields.get("password"):
            fields["password"] = encrypt(fields["password"])
        self.db.update_proxy(proxy_id, **fields)

    def delete_proxy(self, proxy_id: int) -> None:
        self.db.delete_proxy(proxy_id)

    def check_proxy(self, proxy_id: int) -> None:
        proxy = self.db.get_proxy(proxy_id)
        if not proxy:
            return
        # Lightweight check: attempt to build proxy config and resolve host.
        import socket

        host = proxy["host"]
        port = int(proxy["port"])
        try:
            socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
            self.db.set_proxy_status(proxy_id, "ok", last_check=_iso_now())
        except OSError as exc:
            self.db.set_proxy_status(proxy_id, "error", error_message=str(exc))

    def test_connection(self, proxy_id: int) -> None:
        self.check_proxy(proxy_id)


def _iso_now() -> str:
    from datetime import datetime

    return datetime.now(UTC).isoformat()
