"""Tests for envault.search."""

from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from envault.search import SearchError, SearchMatch, search_vaults


@pytest.fixture()
def fernet_key() -> bytes:
    return Fernet.generate_key()


@pytest.fixture()
def fernet(fernet_key: bytes) -> Fernet:
    return Fernet(fernet_key)


@pytest.fixture()
def base_dir(tmp_path: Path, fernet: Fernet) -> Path:
    vault_dir = tmp_path / "vaults"
    vault_dir.mkdir()

    # seed two vaults
    env_a = b"DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n"
    env_b = b"API_KEY=xyz789\nDEBUG=true\n"

    (vault_dir / "project_a.vault").write_bytes(fernet.encrypt(env_a))
    (vault_dir / "project_b.vault").write_bytes(fernet.encrypt(env_b))

    return tmp_path


def test_search_returns_matches_by_key(base_dir: Path, fernet: Fernet) -> None:
    results = search_vaults(base_dir, fernet, "DB")
    keys = [m.key for m in results]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys


def test_search_is_case_insensitive(base_dir: Path, fernet: Fernet) -> None:
    results = search_vaults(base_dir, fernet, "db_host")
    assert any(m.key == "DB_HOST" for m in results)


def test_search_returns_correct_vault_name(base_dir: Path, fernet: Fernet) -> None:
    results = search_vaults(base_dir, fernet, "API_KEY")
    assert len(results) == 1
    assert results[0].vault_name == "project_b"


def test_search_values_flag(base_dir: Path, fernet: Fernet) -> None:
    results = search_vaults(base_dir, fernet, "localhost", search_values=True)
    assert any(m.value == "localhost" for m in results)


def test_search_values_not_searched_by_default(base_dir: Path, fernet: Fernet) -> None:
    results = search_vaults(base_dir, fernet, "localhost")
    assert results == []


def test_search_empty_query_raises(base_dir: Path, fernet: Fernet) -> None:
    with pytest.raises(SearchError, match="empty"):
        search_vaults(base_dir, fernet, "")


def test_search_no_vault_dir_returns_empty(tmp_path: Path, fernet: Fernet) -> None:
    results = search_vaults(tmp_path, fernet, "anything")
    assert results == []


def test_search_across_multiple_vaults(base_dir: Path, fernet: Fernet) -> None:
    results = search_vaults(base_dir, fernet, "KEY")
    vault_names = {m.vault_name for m in results}
    assert "project_a" in vault_names
    assert "project_b" in vault_names
