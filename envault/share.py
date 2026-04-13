"""Vault sharing: export an encrypted vault bundle for another passphrase."""

from __future__ import annotations

import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from envault.keystore import _derive_key
from envault.vault import get_vault_path, vault_exists, load_vault


class ShareError(Exception):
    """Raised when a share operation fails."""


def export_shared_bundle(
    base_dir: Path,
    vault_name: str,
    owner_fernet: Fernet,
    recipient_passphrase: str,
) -> bytes:
    """Re-encrypt a vault's plaintext under a recipient passphrase.

    Returns a JSON bundle (bytes) containing the salt and ciphertext.
    """
    if not vault_exists(base_dir, vault_name):
        raise ShareError(f"Vault '{vault_name}' does not exist.")

    plaintext = load_vault(base_dir, vault_name, owner_fernet)

    salt = os.urandom(16)
    recipient_key = _derive_key(recipient_passphrase, salt)
    recipient_fernet = Fernet(recipient_key)
    ciphertext = recipient_fernet.encrypt(plaintext)

    bundle = {
        "vault": vault_name,
        "salt": salt.hex(),
        "ciphertext": ciphertext.decode(),
    }
    return json.dumps(bundle).encode()


def import_shared_bundle(
    bundle_bytes: bytes,
    recipient_passphrase: str,
    dest_dir: Path,
) -> str:
    """Decrypt a shared bundle and write the vault to *dest_dir*.

    Returns the vault name.
    """
    try:
        bundle = json.loads(bundle_bytes)
        vault_name: str = bundle["vault"]
        salt = bytes.fromhex(bundle["salt"])
        ciphertext: str = bundle["ciphertext"]
    except (KeyError, ValueError) as exc:
        raise ShareError(f"Invalid bundle format: {exc}") from exc

    key = _derive_key(recipient_passphrase, salt)
    fernet = Fernet(key)
    try:
        plaintext = fernet.decrypt(ciphertext.encode())
    except InvalidToken as exc:
        raise ShareError("Wrong passphrase for this bundle.") from exc

    dest_dir.mkdir(parents=True, exist_ok=True)
    vault_path = get_vault_path(dest_dir, vault_name)
    vault_path.write_bytes(plaintext)
    return vault_name
