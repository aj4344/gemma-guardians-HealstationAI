"""Encryption at rest (ADR-001).

Key hierarchy: a key-encryption key (KEK) from the environment, a secret file
or the OS keyring wraps one data key per case; each case key encrypts that
case's fields and wraps one key per blob. Destroying a case key makes all of
the case's data unreadable (crypto-shred).

All encryption is AES-256-GCM with random 96-bit nonces; associated data
binds every ciphertext to where it belongs so it cannot be moved elsewhere.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

logger = logging.getLogger("healstation.store")

KEY_BYTES = 32
NONCE_BYTES = 12
TAG_BYTES = 16
KEYRING_SERVICE = "healstation"
KEYRING_USERNAME = "key-encryption-key"


class CryptoError(Exception):
    """Ciphertext could not be authenticated or a key is missing."""


class KeyUnavailableError(CryptoError):
    """No key-encryption key could be loaded."""


def new_key() -> bytes:
    return os.urandom(KEY_BYTES)


def seal(key: bytes, plaintext: bytes, aad: bytes) -> bytes:
    """Encrypt and authenticate; returns nonce ‖ ciphertext ‖ tag."""
    nonce = os.urandom(NONCE_BYTES)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, aad)


def open_sealed(key: bytes, sealed: bytes, aad: bytes) -> bytes:
    if len(sealed) < NONCE_BYTES + TAG_BYTES:
        raise CryptoError("ciphertext too short")
    try:
        return AESGCM(key).decrypt(sealed[:NONCE_BYTES], sealed[NONCE_BYTES:], aad)
    except InvalidTag as error:
        raise CryptoError("authentication failed") from error


def wrap_key(wrapping_key: bytes, key: bytes, context: str) -> bytes:
    return seal(wrapping_key, key, b"wrap:" + context.encode())


def unwrap_key(wrapping_key: bytes, wrapped: bytes, context: str) -> bytes:
    key = open_sealed(wrapping_key, wrapped, b"wrap:" + context.encode())
    if len(key) != KEY_BYTES:
        raise CryptoError("unwrapped key has the wrong length")
    return key


def derive_key(master: bytes, label: str) -> bytes:
    """A purpose-specific sub-key, so the KEK itself is only ever used for wrapping."""
    return HKDF(algorithm=hashes.SHA256(), length=KEY_BYTES, salt=None, info=label.encode()).derive(master)


def keyed_digest(key: bytes, data: bytes) -> str:
    return hmac.new(key, data, hashlib.sha256).hexdigest()


# ── KEK loading ───────────────────────────────────────────────────────────────


@dataclass
class KekSettings:
    env_value: str = ""
    file: Path | None = None
    use_keyring: bool = True
    auto_create: bool = False


def _decode_kek(raw: str, source: str) -> bytes:
    try:
        key = base64.b64decode(raw.strip(), validate=True)
    except (ValueError, TypeError) as error:
        raise KeyUnavailableError(f"{source} is not valid base64") from error
    if len(key) != KEY_BYTES:
        raise KeyUnavailableError(f"{source} must decode to {KEY_BYTES} bytes")
    return key


def _keyring():
    try:
        import keyring
        from keyring.backends import fail

        backend = keyring.get_keyring()
        if isinstance(backend, fail.Keyring):
            return None
        return keyring
    except Exception:
        # No usable keyring backend (headless Linux without Secret Service).
        return None


def _write_key_file(path: Path, key: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, stat.S_IRUSR | stat.S_IWUSR)
    with os.fdopen(fd, "w", encoding="ascii") as handle:
        handle.write(base64.b64encode(key).decode("ascii"))


def load_kek(settings: KekSettings) -> tuple[bytes, str]:
    """Return (key, source). Never logs or returns key material in errors."""
    if settings.env_value:
        return _decode_kek(settings.env_value, "HEALSTATION_KEK"), "env"
    if settings.file and settings.file.is_file():
        return _decode_kek(settings.file.read_text(encoding="ascii"), "KEK_FILE"), "file"
    store = _keyring() if settings.use_keyring else None
    if store is not None:
        try:
            raw = store.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except Exception:
            raw = None
        if raw:
            return _decode_kek(raw, "keyring entry"), "keyring"
    if not settings.auto_create:
        raise KeyUnavailableError(
            "No key-encryption key found. Set HEALSTATION_KEK or KEK_FILE, or store one in the OS keyring."
        )
    key = new_key()
    if store is not None:
        try:
            store.set_password(KEYRING_SERVICE, KEYRING_USERNAME, base64.b64encode(key).decode("ascii"))
            logger.warning("Created a new key-encryption key in the OS keyring.")
            return key, "keyring"
        except Exception:
            logger.warning("OS keyring is not writable; falling back to KEK_FILE.")
    if settings.file is None:
        raise KeyUnavailableError("No keyring and no KEK_FILE configured to store a new key.")
    _write_key_file(settings.file, key)
    logger.warning("Created a new key-encryption key file outside the data directory.")
    return key, "file"
