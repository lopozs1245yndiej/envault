"""Unit tests for envault.verify."""

from __future__ import annotations

import pytest
from pathlib import Path

from cryptography.fernet import Fernet

from envault.vault import encrypt_env, save_vault, get_vault_path
from envault.verify import (
    VerifyError,
    VerifyResult,
    _checksum,
    get_checksum_path,
    record_checksum,
    verify_vault,
)


@pytest.fixture()
def fernet_key() -> bytes:
    return Fernet.generate_key()


@pytest.fixture()
def vault_dir(tmp_path: Path, fernet_key: bytes) -> Path:
    f = Fernet(fernet_key)
    env_bytes = b"KEY=value\nFOO=bar\n"
    encrypted = encrypt_env(env_bytes, f)
    save_vault(tmp_path, "default", encrypted)
    return tmp_path


def test_get_checksum_path_returns_expected(tmp_path: Path) -> None:
    p = get_checksum_path(tmp_path)
    assert p == tmp_path / ".envault" / "checksums.json"


def test_record_checksum_creates_entry(vault_dir: Path) -> None:
    digest = record_checksum(vault_dir, "default")
    assert len(digest) == 64  # sha256 hex
    path = get_checksum_path(vault_dir)
    assert path.exists()


def test_record_checksum_raises_if_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(VerifyError, match="not found"):
        record_checksum(tmp_path, "ghost")


def test_verify_returns_ok_when_unchanged(vault_dir: Path) -> None:
    record_checksum(vault_dir, "default")
    result = verify_vault(vault_dir, "default")
    assert isinstance(result, VerifyResult)
    assert result.ok is True
    assert result.tampered is False


def test_verify_detects_tampering(vault_dir: Path) -> None:
    record_checksum(vault_dir, "default")
    vault_path = get_vault_path(vault_dir, "default")
    # corrupt the file
    vault_path.write_bytes(b"corrupted data")
    result = verify_vault(vault_dir, "default")
    assert result.ok is False
    assert result.tampered is True
    assert result.expected != result.actual


def test_verify_raises_without_recorded_checksum(vault_dir: Path) -> None:
    with pytest.raises(VerifyError, match="No recorded checksum"):
        verify_vault(vault_dir, "default")


def test_verify_raises_if_vault_missing(tmp_path: Path) -> None:
    with pytest.raises(VerifyError, match="not found"):
        verify_vault(tmp_path, "missing")


def test_checksum_is_deterministic() -> None:
    data = b"hello world"
    assert _checksum(data) == _checksum(data)
    assert _checksum(data) != _checksum(b"other")
