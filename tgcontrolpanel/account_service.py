"""Account service: CRUD and connection orchestration over Database + ClientManager."""
from __future__ import annotations

from typing import Any

from .crypto import encrypt
from .db import Database


class AccountService:
    def __init__(self, db: Database, client_manager) -> None:
        self.db = db
        self.cm = client_manager

    def list_accounts(self) -> list[dict[str, Any]]:
        return self.db.get_accounts()

    def add_account(
        self,
        name: str,
        phone: str | None,
        api_id: str | None,
        api_hash: str | None,
        session_file: str | None,
        proxy_id: int | None = None,
    ) -> int:
        return self.db.add_account(
            name=name,
            phone=phone,
            api_id=encrypt(api_id) if api_id else None,
            api_hash=encrypt(api_hash) if api_hash else None,
            session_file=session_file,
            proxy_id=proxy_id,
        )

    def get_account(self, account_id: int) -> dict[str, Any] | None:
        return self.db.get_account(account_id)

    def update_account(self, account_id: int, **fields: Any) -> None:
        crypto_fields = {}
        if fields.get("api_id"):
            crypto_fields["api_id"] = encrypt(fields.pop("api_id"))
        if fields.get("api_hash"):
            crypto_fields["api_hash"] = encrypt(fields.pop("api_hash"))
        all_fields = {**fields, **crypto_fields}
        self.db.update_account(account_id, **all_fields)

    def delete_account(self, account_id: int) -> None:
        self.cm.disconnect_account(account_id)
        self.db.delete_account(account_id)
        self.db.add_event("account_deleted", message=f"Account {account_id} removed")

    def connect_account(self, account_id: int) -> None:
        self.db.add_event("account_connect", message=f"Connecting account {account_id}", account_id=account_id)
        self.cm.connect_account(account_id)

    def disconnect_account(self, account_id: int) -> None:
        self.cm.disconnect_account(account_id)
        self.db.add_event("account_disconnect", message=f"Disconnected account {account_id}", account_id=account_id)

    def check_connection(self, account_id: int) -> None:
        self.cm.check_connection(account_id)

    def set_proxy(self, account_id: int, proxy_id: int | None) -> None:
        self.db.update_account(account_id, proxy_id=proxy_id)
        self.db.add_event(
            "proxy_assigned",
            message=f"Proxy {proxy_id} assigned to account {account_id}",
            account_id=account_id,
        )
