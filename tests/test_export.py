"""Tests for envault/export.py"""

import json
import pytest
from pathlib import Path
from cryptography.fernet import Fernet

from envault.export import (
    parse_env_bytes,
    export_to_json,
    export_to_dotenv,
    export_to_shell,
)
from envault.vault import encrypt_env, save_vault, get_vault_path


SAMPLE_ENV = b"DB_HOST=localhost\nDB_PORT=5432\n# a comment\nSECRET_KEY=abc123\n"


@pytest.fixture
def fernet_key():
    return Fernet.generate_key()


@pytest.fixture
def fernet(fernet_key):
    return Fernet(fernet_key)


@pytest.fixture
def vault_dir(tmp_path, fernet, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    env_file = tmp_path / ".env"
    env_file.write_bytes(SAMPLE_ENV)
    encrypted = encrypt_env(fernet, env_file)
    save_vault(encrypted, "myapp", base_dir=tmp_path)
    return tmp_path


def test_parse_env_bytes_returns_dict():
    result = parse_env_bytes(SAMPLE_ENV)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "abc123"}


def test_parse_env_bytes_ignores_comments():
    result = parse_env_bytes(SAMPLE_ENV)
    assert all(not k.startswith("#") for k in result)


def test_parse_env_bytes_skips_blank_lines():
    data = b"\nFOO=bar\n\nBAZ=qux\n"
    result = parse_env_bytes(data)
    assert len(result) == 2


def test_export_to_json_creates_file(vault_dir, fernet, tmp_path):
    out = tmp_path / "output.json"
    export_to_json(fernet, "myapp", out)
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["DB_HOST"] == "localhost"


def test_export_to_dotenv_creates_file(vault_dir, fernet, tmp_path):
    out = tmp_path / "exported.env"
    export_to_dotenv(fernet, "myapp", out)
    assert out.exists()
    assert b"DB_HOST=localhost" in out.read_bytes()


def test_export_to_shell_returns_export_statements(vault_dir, fernet):
    result = export_to_shell(fernet, "myapp")
    assert 'export DB_HOST="localhost"' in result
    assert 'export SECRET_KEY="abc123"' in result


def test_export_to_shell_format(vault_dir, fernet):
    result = export_to_shell(fernet, "myapp")
    for line in result.strip().splitlines():
        assert line.startswith("export ")
