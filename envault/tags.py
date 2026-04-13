"""Tag management for vault entries — lets users label vaults with arbitrary tags."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

TAGS_FILENAME = ".envault_tags.json"


class TagError(Exception):
    pass


def get_tags_path(base_dir: Path) -> Path:
    return base_dir / TAGS_FILENAME


def _load_tags(base_dir: Path) -> dict:
    path = get_tags_path(base_dir)
    if not path.exists():
        return {}
    with path.open("r") as f:
        return json.load(f)


def _save_tags(base_dir: Path, data: dict) -> None:
    path = get_tags_path(base_dir)
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def add_tag(base_dir: Path, vault_name: str, tag: str) -> None:
    """Add a tag to a named vault entry."""
    if not tag.strip():
        raise TagError("Tag must not be empty.")
    data = _load_tags(base_dir)
    tags = data.get(vault_name, [])
    if tag not in tags:
        tags.append(tag)
    data[vault_name] = tags
    _save_tags(base_dir, data)


def remove_tag(base_dir: Path, vault_name: str, tag: str) -> None:
    """Remove a tag from a named vault entry."""
    data = _load_tags(base_dir)
    tags = data.get(vault_name, [])
    if tag not in tags:
        raise TagError(f"Tag '{tag}' not found on vault '{vault_name}'.")
    tags.remove(tag)
    data[vault_name] = tags
    _save_tags(base_dir, data)


def get_tags(base_dir: Path, vault_name: str) -> List[str]:
    """Return all tags for a vault entry."""
    data = _load_tags(base_dir)
    return data.get(vault_name, [])


def find_by_tag(base_dir: Path, tag: str) -> List[str]:
    """Return all vault names that carry the given tag."""
    data = _load_tags(base_dir)
    return [name for name, tags in data.items() if tag in tags]


def clear_tags(base_dir: Path, vault_name: str) -> None:
    """Remove all tags for a vault entry."""
    data = _load_tags(base_dir)
    data.pop(vault_name, None)
    _save_tags(base_dir, data)
