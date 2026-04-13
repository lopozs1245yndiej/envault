"""Tests for envault/config.py"""

import json
import pytest
from pathlib import Path

from envault.config import (
    get_config_path,
    config_exists,
    init_config,
    load_config,
    update_config,
    DEFAULT_CONFIG,
)


@pytest.fixture
def config_dir(tmp_path):
    return tmp_path / ".envault"


def test_get_config_path_returns_expected(config_dir):
    path = get_config_path(config_dir)
    assert path == config_dir / "config.json"


def test_config_exists_false_when_missing(config_dir):
    assert config_exists(config_dir) is False


def test_config_exists_true_after_init(config_dir):
    init_config(config_dir)
    assert config_exists(config_dir) is True


def test_init_config_creates_file(config_dir):
    config = init_config(config_dir)
    config_path = get_config_path(config_dir)
    assert config_path.exists()
    assert isinstance(config, dict)


def test_init_config_contains_defaults(config_dir):
    config = init_config(config_dir)
    for key in DEFAULT_CONFIG:
        assert key in config


def test_init_config_raises_if_already_exists(config_dir):
    init_config(config_dir)
    with pytest.raises(FileExistsError):
        init_config(config_dir)


def test_init_config_applies_overrides(config_dir):
    config = init_config(config_dir, overrides={"auto_backup": True})
    assert config["auto_backup"] is True


def test_load_config_returns_defaults_when_missing(config_dir):
    config = load_config(config_dir)
    assert config == DEFAULT_CONFIG


def test_load_config_reads_from_disk(config_dir):
    init_config(config_dir, overrides={"default_env_file": ".env.local"})
    config = load_config(config_dir)
    assert config["default_env_file"] == ".env.local"


def test_load_config_merges_missing_defaults(config_dir, tmp_path):
    # Write a partial config without all keys
    config_dir.mkdir(parents=True)
    partial = {"auto_backup": True}
    (config_dir / "config.json").write_text(json.dumps(partial))
    config = load_config(config_dir)
    assert "sync_dir" in config
    assert config["auto_backup"] is True


def test_update_config_modifies_key(config_dir):
    init_config(config_dir)
    updated = update_config({"auto_backup": True}, config_dir)
    assert updated["auto_backup"] is True
    # Verify persisted
    reloaded = load_config(config_dir)
    assert reloaded["auto_backup"] is True


def test_update_config_creates_file_if_missing(config_dir):
    updated = update_config({"auto_backup": True}, config_dir)
    assert get_config_path(config_dir).exists()
    assert updated["auto_backup"] is True
