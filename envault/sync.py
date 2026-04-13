"""Sync vault files to/from a remote location (local path or future remote)."""

import os
import shutil
from pathlib import Path
from datetime import datetime

DEFAULT_SYNC_DIR = Path.home() / ".envault" / "sync"


def get_sync_dir() -> Path:
    """Return the sync directory, respecting ENVAULT_SYNC_DIR env var."""
    return Path(os.environ.get("ENVAULT_SYNC_DIR", DEFAULT_SYNC_DIR))


def ensure_sync_dir(sync_dir: Path | None = None) -> Path:
    """Create sync directory if it doesn't exist."""
    target = sync_dir or get_sync_dir()
    target.mkdir(parents=True, exist_ok=True)
    return target


def push_vault(vault_path: Path, sync_dir: Path | None = None) -> Path:
    """Copy a vault file into the sync directory.

    Args:
        vault_path: Path to the local .vault file.
        sync_dir: Optional override for sync destination.

    Returns:
        Path to the synced copy.

    Raises:
        FileNotFoundError: If vault_path does not exist.
    """
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault file not found: {vault_path}")

    target_dir = ensure_sync_dir(sync_dir)
    dest = target_dir / vault_path.name
    shutil.copy2(vault_path, dest)
    return dest


def pull_vault(vault_name: str, dest_dir: Path, sync_dir: Path | None = None) -> Path:
    """Copy a vault file from the sync directory to a local destination.

    Args:
        vault_name: Filename of the vault (e.g. ".env.vault").
        dest_dir: Directory where the vault should be written.
        sync_dir: Optional override for sync source.

    Returns:
        Path to the pulled vault file.

    Raises:
        FileNotFoundError: If the vault does not exist in sync dir.
    """
    source_dir = sync_dir or get_sync_dir()
    source = source_dir / vault_name

    if not source.exists():
        raise FileNotFoundError(f"No synced vault found for '{vault_name}'")

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / vault_name
    shutil.copy2(source, dest)
    return dest


def list_synced_vaults(sync_dir: Path | None = None) -> list[str]:
    """Return names of all vault files in the sync directory."""
    target = sync_dir or get_sync_dir()
    if not target.exists():
        return []
    return sorted(p.name for p in target.iterdir() if p.suffix == ".vault")
