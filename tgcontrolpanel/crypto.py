"""Encrypted storage for sensitive data (api_id, api_hash, proxy credentials)."""
from __future__ import annotations

import os

from cryptography.fernet import Fernet, InvalidToken

from .config import KEY_PATH


def _load_or_create_key() -> bytes:
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if KEY_PATH.exists():
        return KEY_PATH.read_bytes()
    key = Fernet.generate_key()
    KEY_PATH.write_bytes(key)
    try:
        os.chmod(KEY_PATH, 0o600)
    except OSError:
        pass
    return key


_KEY = _load_or_create_key()
_FERNET = Fernet(_KEY)


def encrypt(value: str | None) -> str | None:
    if value is None or value == "":
        return value
    return _FERNET.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt(value: str | None) -> str | None:
    if value is None or value == "":
        return value
    try:
        return _FERNET.decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return value


def encrypt_bytes(value: bytes | None) -> bytes | None:
    if value is None:
        return None
    return _FERNET.encrypt(value)


def decrypt_bytes(value: bytes | None) -> bytes | None:
    if value is None:
        return None
    try:
        return _FERNET.decrypt(value)
    except (InvalidToken, ValueError):
        return value
