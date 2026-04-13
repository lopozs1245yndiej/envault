"""Unit tests for envault.diff."""

import os
import pytest
from cryptography.fernet import Fernet

from envault.diff import DiffEntry, DiffError, diff_env, format_diff
from envault.vault import encrypt_env, save_vault


@pytest.fixture
def fernet_key():
    return Fernet.generate_key()


@pytest.fixture
def fernet(fernet_key):
    return Fernet(fernet_key)


@pytest.fixture
def vault_dir(tmp_path):
    d = tmp_path / "vaults"
    d.mkdir()
    return str(d)


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("KEY_A=hello\nKEY_B=world\nKEY_C=local_only\n")
    return str(p)


def _seed_vault(fernet, vault_dir, name, content: str):
    raw = content.encode()
    token = fernet.encrypt(raw)
    path = os.path.join(vault_dir, f"{name}.vault")
    with open(path, "wb") as fh:
        fh.write(token)


def test_diff_unchanged(fernet, vault_dir, env_file):
    _seed_vault(fernet, vault_dir, "myapp", "KEY_A=hello\nKEY_B=world\nKEY_C=local_only\n")
    entries = diff_env(env_file, "myapp", fernet, vault_dir)
    assert all(e.status == "unchanged" for e in entries)


def test_diff_detects_added(fernet, vault_dir, env_file):
    _seed_vault(fernet, vault_dir, "myapp", "KEY_A=hello\nKEY_B=world\n")
    entries = diff_env(env_file, "myapp", fernet, vault_dir)
    added = [e for e in entries if e.status == "added"]
    assert len(added) == 1
    assert added[0].key == "KEY_C"


def test_diff_detects_removed(fernet, vault_dir, env_file):
    _seed_vault(fernet, vault_dir, "myapp", "KEY_A=hello\nKEY_B=world\nKEY_C=local_only\nKEY_D=vault_only\n")
    entries = diff_env(env_file, "myapp", fernet, vault_dir)
    removed = [e for e in entries if e.status == "removed"]
    assert len(removed) == 1
    assert removed[0].key == "KEY_D"


def test_diff_detects_changed(fernet, vault_dir, env_file):
    _seed_vault(fernet, vault_dir, "myapp", "KEY_A=hello\nKEY_B=different\nKEY_C=local_only\n")
    entries = diff_env(env_file, "myapp", fernet, vault_dir)
    changed = [e for e in entries if e.status == "changed"]
    assert len(changed) == 1
    assert changed[0].key == "KEY_B"
    assert changed[0].local_value == "world"
    assert changed[0].vault_value == "different"


def test_diff_raises_if_vault_missing(fernet, vault_dir, env_file):
    with pytest.raises(DiffError, match="does not exist"):
        diff_env(env_file, "nonexistent", fernet, vault_dir)


def test_diff_raises_if_env_missing(fernet, vault_dir, tmp_path):
    _seed_vault(fernet, vault_dir, "myapp", "KEY_A=hello\n")
    with pytest.raises(DiffError, match="not found"):
        diff_env(str(tmp_path / "missing.env"), "myapp", fernet, vault_dir)


def test_format_diff_symbols():
    entries = [
        DiffEntry(key="A", status="added", local_value="1"),
        DiffEntry(key="B", status="removed", vault_value="2"),
        DiffEntry(key="C", status="changed", local_value="x", vault_value="y"),
        DiffEntry(key="D", status="unchanged", local_value="z", vault_value="z"),
    ]
    output = format_diff(entries)
    assert output.startswith("+ A")
    assert "- B" in output
    assert "~ C" in output
    assert "  D" in output


def test_format_diff_show_values():
    entries = [DiffEntry(key="X", status="changed", local_value="new", vault_value="old")]
    output = format_diff(entries, show_values=True)
    assert "new" in output
    assert "old" in output
