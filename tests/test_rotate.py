"""Tests for envault.rotate passphrase rotation."""

import pytest
from pathlib import Path
from cryptography.fernet import Fernet

from envault.keystore import init_keystore, load_keystore
from envault.vault import save_vault, load_vault
from envault.rotate import rotate_passphrase, RotationError


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    envault_dir = tmp_path / ".envault"
    envault_dir.mkdir()
    (tmp_path / "vaults").mkdir()
    return tmp_path


@pytest.fixture
def initialised_base(base_dir: Path):
    """Base dir with a keystore already initialised."""
    init_keystore(base_dir, "old-secret")
    return base_dir


def test_rotate_fails_without_keystore(tmp_path: Path):
    (tmp_path / ".envault").mkdir()
    with pytest.raises(RotationError, match="No keystore found"):
        rotate_passphrase(tmp_path, "old", "new")


def test_rotate_fails_with_wrong_old_passphrase(initialised_base: Path):
    with pytest.raises(RotationError, match="Failed to unlock"):
        rotate_passphrase(initialised_base, "wrong-passphrase", "new-secret")


def test_rotate_changes_passphrase(initialised_base: Path):
    rotate_passphrase(initialised_base, "old-secret", "new-secret")

    # Old passphrase should no longer work
    with pytest.raises(Exception):
        load_keystore(initialised_base, "old-secret")

    # New passphrase should work
    fernet = load_keystore(initialised_base, "new-secret")
    assert fernet is not None


def test_rotate_re_encrypts_vaults(initialised_base: Path):
    old_fernet = load_keystore(initialised_base, "old-secret")
    plaintext = b"API_KEY=abc123\nDEBUG=true\n"
    encrypted = old_fernet.encrypt(plaintext)
    save_vault(initialised_base, "myapp", encrypted)

    rotated = rotate_passphrase(initialised_base, "old-secret", "new-secret", vault_names=["myapp"])

    assert "myapp" in rotated

    new_fernet = load_keystore(initialised_base, "new-secret")
    re_encrypted = load_vault(initialised_base, "myapp")
    assert new_fernet.decrypt(re_encrypted) == plaintext


def test_rotate_raises_if_vault_missing(initialised_base: Path):
    with pytest.raises(RotationError, match="not found"):
        rotate_passphrase(initialised_base, "old-secret", "new-secret", vault_names=["ghost"])


def test_rotate_returns_empty_list_when_no_vaults(initialised_base: Path):
    result = rotate_passphrase(initialised_base, "old-secret", "new-secret")
    assert result == []


def test_rotate_writes_audit_log(initialised_base: Path):
    from envault.audit import read_events
    rotate_passphrase(initialised_base, "old-secret", "new-secret")
    events = read_events(initialised_base)
    assert any(e["action"] == "rotate" for e in events)
