"""Tests for envault.sync module."""

import pytest
from pathlib import Path
from envault.sync import push_vault, pull_vault, list_synced_vaults, ensure_sync_dir


@pytest.fixture
def sync_dir(tmp_path):
    return tmp_path / "sync"


@pytest.fixture
def vault_file(tmp_path):
    vf = tmp_path / ".env.vault"
    vf.write_bytes(b"encrypted-data-here")
    return vf


def test_ensure_sync_dir_creates_directory(tmp_path):
    target = tmp_path / "new_sync"
    result = ensure_sync_dir(target)
    assert result.exists()
    assert result.is_dir()


def test_push_vault_copies_file(vault_file, sync_dir):
    dest = push_vault(vault_file, sync_dir=sync_dir)
    assert dest.exists()
    assert dest.read_bytes() == b"encrypted-data-here"
    assert dest.name == ".env.vault"


def test_push_vault_raises_if_missing(tmp_path, sync_dir):
    missing = tmp_path / "ghost.vault"
    with pytest.raises(FileNotFoundError, match="Vault file not found"):
        push_vault(missing, sync_dir=sync_dir)


def test_pull_vault_copies_to_dest(tmp_path, vault_file, sync_dir):
    push_vault(vault_file, sync_dir=sync_dir)

    dest_dir = tmp_path / "project"
    pulled = pull_vault(".env.vault", dest_dir, sync_dir=sync_dir)

    assert pulled.exists()
    assert pulled.read_bytes() == b"encrypted-data-here"


def test_pull_vault_raises_if_not_synced(tmp_path, sync_dir):
    with pytest.raises(FileNotFoundError, match="No synced vault found"):
        pull_vault(".env.vault", tmp_path / "dest", sync_dir=sync_dir)


def test_list_synced_vaults_empty(sync_dir):
    assert list_synced_vaults(sync_dir=sync_dir) == []


def test_list_synced_vaults_returns_vault_names(tmp_path, sync_dir):
    for name in (".env.vault", "production.vault", "staging.vault"):
        f = tmp_path / name
        f.write_bytes(b"data")
        push_vault(f, sync_dir=sync_dir)

    result = list_synced_vaults(sync_dir=sync_dir)
    assert result == [".env.vault", "production.vault", "staging.vault"]


def test_list_synced_vaults_ignores_non_vault_files(sync_dir):
    sync_dir.mkdir(parents=True, exist_ok=True)
    (sync_dir / "readme.txt").write_text("not a vault")
    (sync_dir / "notes.md").write_text("also not")
    (sync_dir / "real.vault").write_bytes(b"vault data")

    result = list_synced_vaults(sync_dir=sync_dir)
    assert result == ["real.vault"]
