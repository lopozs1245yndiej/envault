"""Tests for envault.tags and envault.cli_tags."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.tags import (
    TagError,
    add_tag,
    clear_tags,
    find_by_tag,
    get_tags,
    get_tags_path,
    remove_tag,
)
from envault.cli_tags import tags_cli


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


# --- unit tests ---

def test_get_tags_path_returns_expected(base_dir):
    assert get_tags_path(base_dir) == base_dir / ".envault_tags.json"


def test_add_tag_creates_file(base_dir):
    add_tag(base_dir, "myapp", "production")
    assert get_tags_path(base_dir).exists()


def test_add_tag_stores_tag(base_dir):
    add_tag(base_dir, "myapp", "production")
    assert "production" in get_tags(base_dir, "myapp")


def test_add_tag_no_duplicates(base_dir):
    add_tag(base_dir, "myapp", "prod")
    add_tag(base_dir, "myapp", "prod")
    assert get_tags(base_dir, "myapp").count("prod") == 1


def test_add_tag_empty_raises(base_dir):
    with pytest.raises(TagError):
        add_tag(base_dir, "myapp", "   ")


def test_remove_tag_works(base_dir):
    add_tag(base_dir, "myapp", "staging")
    remove_tag(base_dir, "myapp", "staging")
    assert "staging" not in get_tags(base_dir, "myapp")


def test_remove_tag_missing_raises(base_dir):
    with pytest.raises(TagError):
        remove_tag(base_dir, "myapp", "nonexistent")


def test_find_by_tag_returns_matching(base_dir):
    add_tag(base_dir, "app1", "dev")
    add_tag(base_dir, "app2", "prod")
    add_tag(base_dir, "app3", "dev")
    result = find_by_tag(base_dir, "dev")
    assert set(result) == {"app1", "app3"}


def test_clear_tags_removes_all(base_dir):
    add_tag(base_dir, "myapp", "a")
    add_tag(base_dir, "myapp", "b")
    clear_tags(base_dir, "myapp")
    assert get_tags(base_dir, "myapp") == []


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_add_success(runner, base_dir):
    result = runner.invoke(tags_cli, ["add", "myapp", "prod", "--base-dir", str(base_dir)])
    assert result.exit_code == 0
    assert "added" in result.output


def test_cli_list_shows_tags(runner, base_dir):
    add_tag(base_dir, "myapp", "prod")
    result = runner.invoke(tags_cli, ["list", "myapp", "--base-dir", str(base_dir)])
    assert "prod" in result.output


def test_cli_find_shows_vaults(runner, base_dir):
    add_tag(base_dir, "app1", "dev")
    result = runner.invoke(tags_cli, ["find", "dev", "--base-dir", str(base_dir)])
    assert "app1" in result.output


def test_cli_remove_missing_tag_exits_nonzero(runner, base_dir):
    result = runner.invoke(tags_cli, ["remove", "myapp", "ghost", "--base-dir", str(base_dir)])
    assert result.exit_code != 0
