"""Passphrase-protected local keystore for managing encryption keys."""

import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.fernet import Fernet
import base64
import secrets

DEFAULT_KEYSTORE_PATH = Path.home() / ".envault" / "keystore.json"


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a passphrase using Scrypt."""
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    raw = kdf.derive(passphrase.encode())
    return base64.urlsafe_b64encode(raw)


def init_keystore(passphrase: str, path: Path = DEFAULT_KEYSTORE_PATH) -> None:
    """Initialize a new keystore protected by the given passphrase."""
    if path.exists():
        raise FileExistsError(f"Keystore already exists at {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    salt = secrets.token_bytes(16)
    encryption_key = Fernet.generate_key()
    derived = _derive_key(passphrase, salt)
    token = Fernet(derived).encrypt(encryption_key)

    data = {
        "salt": base64.b64encode(salt).decode(),
        "token": base64.b64encode(token).decode(),
    }
    path.write_text(json.dumps(data, indent=2))
    os.chmod(path, 0o600)


def load_keystore(passphrase: str, path: Path = DEFAULT_KEYSTORE_PATH) -> Fernet:
    """Unlock the keystore and return a Fernet instance for encryption/decryption."""
    if not path.exists():
        raise FileNotFoundError(f"No keystore found at {path}. Run 'envault init' first.")

    data = json.loads(path.read_text())
    salt = base64.b64decode(data["salt"])
    token = base64.b64decode(data["token"])
    derived = _derive_key(passphrase, salt)

    try:
        encryption_key = Fernet(derived).decrypt(token)
    except Exception:
        raise ValueError("Invalid passphrase.")

    return Fernet(encryption_key)


def keystore_exists(path: Path = DEFAULT_KEYSTORE_PATH) -> bool:
    return path.exists()
