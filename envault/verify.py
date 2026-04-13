"""Verify integrity of vault files using stored checksums."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet

from envault.vault import get_vault_path, vault_exists, load_vault


class VerifyError(Exception):
    pass


@dataclass
class VerifyResult:
    vault_name: str
    ok: bool
    expected: str
    actual: str

    @property
    def tampered(self) -> bool:
        return not self.ok


def _checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_checksum_path(base_dir: Path) -> Path:
    return base_dir / ".envault" / "checksums.json"


def _load_checksums(base_dir: Path) -> dict[str, str]:
    path = get_checksum_path(base_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_checksums(base_dir: Path, data: dict[str, str]) -> None:
    path = get_checksum_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def record_checksum(base_dir: Path, vault_name: str) -> str:
    """Store a checksum for the current state of a vault."""
    vault_path = get_vault_path(base_dir, vault_name)
    if not vault_path.exists():
        raise VerifyError(f"Vault '{vault_name}' not found.")
    data = vault_path.read_bytes()
    digest = _checksum(data)
    checksums = _load_checksums(base_dir)
    checksums[vault_name] = digest
    _save_checksums(base_dir, checksums)
    return digest


def verify_vault(base_dir: Path, vault_name: str) -> VerifyResult:
    """Compare current vault checksum against the recorded one."""
    vault_path = get_vault_path(base_dir, vault_name)
    if not vault_path.exists():
        raise VerifyError(f"Vault '{vault_name}' not found.")
    checksums = _load_checksums(base_dir)
    if vault_name not in checksums:
        raise VerifyError(f"No recorded checksum for '{vault_name}'.")
    actual = _checksum(vault_path.read_bytes())
    expected = checksums[vault_name]
    return VerifyResult(
        vault_name=vault_name,
        ok=actual == expected,
        expected=expected,
        actual=actual,
    )
