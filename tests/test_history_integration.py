"""Integration tests for history: full snapshot/restore cycle."""

import pytest
from pathlib import Path
from cryptography.fernet import Fernet

from envault.history import save_snapshot, list_snapshots, restore_snapshot
from envault.vault import encrypt_env, save_vault, decrypt_env, get_vault_path


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def fernet() -> Fernet:
    return Fernet(Fernet.generate_key())


@pytest.fixture
def env_file(base_dir: Path) -> Path:
    p = base_dir / ".env"
    p.write_text("DB=postgres\nSECRET=abc123\n")
    return p


def test_snapshot_then_restore_preserves_content(base_dir, fernet, env_file):
    vault_path = get_vault_path(base_dir, "myenv")
    encrypted = encrypt_env(fernet, env_file)
    save_vault(base_dir, "myenv", encrypted)

    save_snapshot(base_dir, vault_path, "myenv", note="v1")

    # Overwrite vault with different content
    env_file.write_text("DB=mysql\nSECRET=changed\n")
    encrypted2 = encrypt_env(fernet, env_file)
    save_vault(base_dir, "myenv", encrypted2)

    # Restore from snapshot 0
    restore_snapshot(base_dir, "myenv", 0, vault_path)
    restored_data = decrypt_env(fernet, vault_path)
    assert b"DB=postgres" in restored_data
    assert b"SECRET=abc123" in restored_data


def test_multiple_vaults_have_independent_histories(base_dir, fernet, env_file):
    for name in ("alpha", "beta"):
        vault_path = get_vault_path(base_dir, name)
        encrypted = encrypt_env(fernet, env_file)
        save_vault(base_dir, name, encrypted)
        save_snapshot(base_dir, vault_path, name)
        save_snapshot(base_dir, vault_path, name)

    assert len(list_snapshots(base_dir, "alpha")) == 2
    assert len(list_snapshots(base_dir, "beta")) == 2


def test_snapshot_index_is_monotonically_increasing(base_dir, fernet, env_file):
    vault_path = get_vault_path(base_dir, "myenv")
    encrypted = encrypt_env(fernet, env_file)
    save_vault(base_dir, "myenv", encrypted)

    metas = [save_snapshot(base_dir, vault_path, "myenv") for _ in range(5)]
    indices = [m.index for m in metas]
    assert indices == sorted(indices)
    assert len(set(indices)) == 5
