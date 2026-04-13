"""Tests for envault.history snapshot module."""

import pytest
from pathlib import Path
from cryptography.fernet import Fernet

from envault.history import (
    save_snapshot,
    list_snapshots,
    restore_snapshot,
    get_history_dir,
    MAX_SNAPSHOTS,
)


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def vault_file(base_dir: Path) -> Path:
    key = Fernet.generate_key()
    f = Fernet(key)
    vault = base_dir / "test.vault"
    vault.write_bytes(f.encrypt(b"SECRET=hello"))
    return vault


def test_save_snapshot_creates_history_dir(base_dir, vault_file):
    save_snapshot(base_dir, vault_file, "test")
    assert get_history_dir(base_dir).exists()


def test_save_snapshot_returns_meta(base_dir, vault_file):
    meta = save_snapshot(base_dir, vault_file, "test", note="initial")
    assert meta.vault_name == "test"
    assert meta.index == 0
    assert meta.note == "initial"
    assert meta.timestamp


def test_save_snapshot_increments_index(base_dir, vault_file):
    m1 = save_snapshot(base_dir, vault_file, "test")
    m2 = save_snapshot(base_dir, vault_file, "test")
    assert m2.index == m1.index + 1


def test_save_snapshot_raises_if_vault_missing(base_dir, tmp_path):
    with pytest.raises(FileNotFoundError):
        save_snapshot(base_dir, tmp_path / "ghost.vault", "ghost")


def test_list_snapshots_returns_correct_vault(base_dir, vault_file):
    save_snapshot(base_dir, vault_file, "alpha")
    save_snapshot(base_dir, vault_file, "beta")
    save_snapshot(base_dir, vault_file, "alpha")
    results = list_snapshots(base_dir, "alpha")
    assert len(results) == 2
    assert all(s.vault_name == "alpha" for s in results)


def test_list_snapshots_empty_when_none(base_dir):
    assert list_snapshots(base_dir, "nonexistent") == []


def test_restore_snapshot_writes_file(base_dir, vault_file):
    save_snapshot(base_dir, vault_file, "test")
    dest = base_dir / "restored.vault"
    restore_snapshot(base_dir, "test", 0, dest)
    assert dest.exists()
    assert dest.read_bytes() == vault_file.read_bytes()


def test_restore_snapshot_raises_if_missing(base_dir):
    with pytest.raises(FileNotFoundError):
        restore_snapshot(base_dir, "ghost", 99, base_dir / "out.vault")


def test_snapshot_pruning_respects_max(base_dir, vault_file):
    for _ in range(MAX_SNAPSHOTS + 5):
        save_snapshot(base_dir, vault_file, "test")
    snapshots = list_snapshots(base_dir, "test")
    assert len(snapshots) <= MAX_SNAPSHOTS
