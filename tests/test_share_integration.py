"""Integration tests for the full share export/import cycle."""

from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from envault.share import export_shared_bundle, import_shared_bundle
from envault.vault import save_vault, get_vault_path


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path / "owner"


@pytest.fixture()
def fernet() -> Fernet:
    return Fernet(Fernet.generate_key())


@pytest.fixture()
def env_content() -> bytes:
    return b"API_KEY=supersecret\nDEBUG=false\nPORT=8080\n"


def test_full_share_cycle(base_dir: Path, fernet: Fernet, env_content: bytes, tmp_path: Path) -> None:
    save_vault(base_dir, "webapp", fernet, env_content)
    bundle = export_shared_bundle(base_dir, "webapp", fernet, "friend-pass")

    dest = tmp_path / "friend"
    vault_name = import_shared_bundle(bundle, "friend-pass", dest)
    assert vault_name == "webapp"

    imported_path = get_vault_path(dest, vault_name)
    assert imported_path.exists()
    assert imported_path.read_bytes() == env_content


def test_different_recipients_get_independent_bundles(
    base_dir: Path, fernet: Fernet, env_content: bytes, tmp_path: Path
) -> None:
    save_vault(base_dir, "webapp", fernet, env_content)

    bundle_a = export_shared_bundle(base_dir, "webapp", fernet, "alice-pass")
    bundle_b = export_shared_bundle(base_dir, "webapp", fernet, "bob-pass")

    # Bundles should differ (different salts / ciphertexts)
    assert bundle_a != bundle_b

    dest_a = tmp_path / "alice"
    dest_b = tmp_path / "bob"
    import_shared_bundle(bundle_a, "alice-pass", dest_a)
    import_shared_bundle(bundle_b, "bob-pass", dest_b)

    content_a = get_vault_path(dest_a, "webapp").read_bytes()
    content_b = get_vault_path(dest_b, "webapp").read_bytes()
    assert content_a == content_b == env_content


def test_bundle_cannot_be_decrypted_with_wrong_passphrase(
    base_dir: Path, fernet: Fernet, env_content: bytes, tmp_path: Path
) -> None:
    from envault.share import ShareError

    save_vault(base_dir, "webapp", fernet, env_content)
    bundle = export_shared_bundle(base_dir, "webapp", fernet, "correct")

    with pytest.raises(ShareError):
        import_shared_bundle(bundle, "incorrect", tmp_path / "dest")
