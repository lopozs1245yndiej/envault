"""Vault snapshot history — track versions of encrypted vaults."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List

HISTORY_DIR_NAME = ".history"
MAX_SNAPSHOTS = 20


@dataclass
class SnapshotMeta:
    index: int
    timestamp: str
    vault_name: str
    note: str = ""


def get_history_dir(base_dir: Path) -> Path:
    return base_dir / HISTORY_DIR_NAME


def _meta_path(history_dir: Path) -> Path:
    return history_dir / "meta.json"


def _load_meta(history_dir: Path) -> List[dict]:
    p = _meta_path(history_dir)
    if not p.exists():
        return []
    return json.loads(p.read_text())


def _save_meta(history_dir: Path, entries: List[dict]) -> None:
    _meta_path(history_dir).write_text(json.dumps(entries, indent=2))


def save_snapshot(base_dir: Path, vault_path: Path, vault_name: str, note: str = "") -> SnapshotMeta:
    """Copy the current vault file into the history directory."""
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault not found: {vault_path}")

    history_dir = get_history_dir(base_dir)
    history_dir.mkdir(parents=True, exist_ok=True)

    entries = _load_meta(history_dir)
    next_index = (entries[-1]["index"] + 1) if entries else 0

    snapshot_file = history_dir / f"{vault_name}.{next_index}.vault"
    shutil.copy2(vault_path, snapshot_file)

    meta = SnapshotMeta(
        index=next_index,
        timestamp=datetime.now(timezone.utc).isoformat(),
        vault_name=vault_name,
        note=note,
    )
    entries.append(asdict(meta))

    # Prune old snapshots beyond MAX_SNAPSHOTS
    if len(entries) > MAX_SNAPSHOTS:
        oldest = entries.pop(0)
        old_file = history_dir / f"{oldest['vault_name']}.{oldest['index']}.vault"
        old_file.unlink(missing_ok=True)

    _save_meta(history_dir, entries)
    return meta


def list_snapshots(base_dir: Path, vault_name: str) -> List[SnapshotMeta]:
    history_dir = get_history_dir(base_dir)
    entries = _load_meta(history_dir)
    return [SnapshotMeta(**e) for e in entries if e["vault_name"] == vault_name]


def restore_snapshot(base_dir: Path, vault_name: str, index: int, dest: Path) -> None:
    history_dir = get_history_dir(base_dir)
    snapshot_file = history_dir / f"{vault_name}.{index}.vault"
    if not snapshot_file.exists():
        raise FileNotFoundError(f"Snapshot {index} not found for vault '{vault_name}'")
    shutil.copy2(snapshot_file, dest)
