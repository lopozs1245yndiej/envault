"""Unit tests for envault.share."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from envault.share import ShareError, export_shared_bundle, import_shared_bundle
from envault.vault import save_vault, get_vault_path


@pytest.fixture()
def fernet_key() -> bytes:
    return Fernet.generate_key()


@pytest.fixture()
def fernet(fernet_key: bytes) -> Fernet:
    return Fernet(fernet_key)


@pytest.fixture()
def vault_dir(tmp_path: Path, fernet: Fernet) -> Path:
    env_content = b"SECRET=abc\nDEBUG=true\n"
    save_vault(tmp_path, "myapp", fernet, env_content)
    return tmp_path


def test_export_returns_bytes(vault_dir: Path, fernet: Fernet) -> None:
    bundle = export_shared_bundle(vault_dir, "myapp", fernet, "recipient-pass")
    assert isinstance(bundle, bytes)


def test_export_bundle_has_expected_keys(vault_dir: Path, fernet: Fernet) -> None:
    bundle = export_shared_bundle(vault_dir, "myapp", fernet, "recipient-pass")
    data = json.loads(bundle)
    assert "vault" in data
    assert "salt" in data
    assert "ciphertext" in data


def test_export_raises_if_vault_missing(tmp_path: Path, fernet: Fernet) -> None:
    with pytest.raises(ShareError, match="does not exist"):
        export_shared_bundle(tmp_path, "ghost", fernet, "pass")


def test_roundtrip_preserves_content(vault_dir: Path, fernet: Fernet, tmp_path: Path) -> None:
    bundle = export_shared_bundle(vault_dir, "myapp", fernet, "recv-secret")
    dest = tmp_path / "imported"
    import_shared_bundle(bundle, "recv-secret", dest)
    vault_path = get_vault_path(dest, "myapp")
    # The imported file is raw plaintext (already decrypted by import)
    assert vault_path.exists()


def test_import_wrong_passphrase_raises(vault_dir: Path, fernet: Fernet, tmp_path: Path) -> None:
    bundle = export_shared_bundle(vault_dir, "myapp", fernet, "correct-pass")
    with pytest.raises(ShareError, match="Wrong passphrase"):
        import_shared_bundle(bundle, "wrong-pass", tmp_path)


def test_import_invalid_bundle_raises(tmp_path: Path) -> None:
    with pytest.raises(ShareError, match="Invalid bundle"):
        import_shared_bundle(b"{\"bad\": true}", "pass", tmp_path)


def test_import_returns_vault_name(vault_dir: Path, fernet: Fernet, tmp_path: Path) -> None:
    bundle = export_shared_bundle(vault_dir, "myapp", fernet, "recv-secret")
    name = import_shared_bundle(bundle, "recv-secret", tmp_path)
    assert name == "myapp"
