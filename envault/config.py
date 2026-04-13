"""Configuration management for envault."""

import json
import os
from pathlib import Path

DEFAULT_CONFIG_DIR = Path.home() / ".envault"
CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "sync_dir": str(DEFAULT_CONFIG_DIR / "synced"),
    "keystore_path": str(DEFAULT_CONFIG_DIR / "keystore.json"),
    "default_env_file": ".env",
    "auto_backup": False,
}


def get_config_path(config_dir: Path = DEFAULT_CONFIG_DIR) -> Path:
    """Return the path to the config file."""
    return config_dir / CONFIG_FILE


def config_exists(config_dir: Path = DEFAULT_CONFIG_DIR) -> bool:
    """Check if a config file exists."""
    return get_config_path(config_dir).exists()


def init_config(config_dir: Path = DEFAULT_CONFIG_DIR, overrides: dict = None) -> dict:
    """Create a new config file with default values, optionally overriding some."""
    config_dir = Path(config_dir)
    config_path = get_config_path(config_dir)

    if config_path.exists():
        raise FileExistsError(f"Config already exists at {config_path}")

    config_dir.mkdir(parents=True, exist_ok=True)

    config = {**DEFAULT_CONFIG}
    if overrides:
        config.update(overrides)

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    return config


def load_config(config_dir: Path = DEFAULT_CONFIG_DIR) -> dict:
    """Load config from disk, falling back to defaults if not found."""
    config_path = get_config_path(config_dir)

    if not config_path.exists():
        return {**DEFAULT_CONFIG}

    with open(config_path, "r") as f:
        data = json.load(f)

    # Merge with defaults so new keys are always present
    return {**DEFAULT_CONFIG, **data}


def update_config(updates: dict, config_dir: Path = DEFAULT_CONFIG_DIR) -> dict:
    """Update specific keys in the config file."""
    config = load_config(config_dir)
    config.update(updates)

    config_path = get_config_path(config_dir)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    return config
