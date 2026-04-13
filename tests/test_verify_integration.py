"""Integration tests for the full record → verify cycle."""

from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from envault.vault import encrypt_env, save_vault, get_vault_path
from envault.verify import record_checksum, verify_vault, VerifyError


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def fernet() -> Fernet:
    return Fernet(Fernet.generate_key())


def _seed(base: Path, name: str, content: bytes, f: Fernet) -> None:
    encrypted = encrypt_env(content, f)
    save_vault(base, name, encrypted)


def test_record_then_verify_ok(base_dir: Path, fernet: Fernet) -> None:
    _seed(base_dir, "prod", b"DB=postgres\n", fernet)
    record_checksum(base_dir, "prod")
    result = verify_vault(base_dir, "prod")
    assert result.ok


def test_verify_fails_after_modification(base_dir: Path, fernet: Fernet) -> None:
    _seed(base_dir, "prod", b"DB=postgres\n", fernet)
    record_checksum(base_dir, "prod")
    # overwrite with different encrypted content
    _seed(base_dir, "prod", b"DB=mysql\n", fernet)
    result = verify_vault(base_dir, "prod")
    assert not result.ok


def test_multiple_vaults_independent(base_dir: Path, fernet: Fernet) -> None:
    _seed(base_dir, "dev", b"ENV=dev\n", fernet)
    _seed(base_dir, "staging", b"ENV=staging\n", fernet)
    record_checksum(base_dir, "dev")
    record_checksum(base_dir, "staging")
    # tamper only dev
    get_vault_path(base_dir, "dev").write_bytes(b"tampered")
    dev_result = verify_vault(base_dir, "dev")
    staging_result = verify_vault(base_dir, "staging")
    assert not dev_result.ok
    assert staging_result.ok


def test_re_record_after_legitimate_update(base_dir: Path, fernet: Fernet) -> None:
    _seed(base_dir, "prod", b"V=1\n", fernet)
    record_checksum(base_dir, "prod")
    # legitimate update
    _seed(base_dir, "prod", b"V=2\n", fernet)
    record_checksum(base_dir, "prod")  # re-record
    result = verify_vault(base_dir, "prod")
    assert result.ok
