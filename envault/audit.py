"""Audit log for envault operations — tracks lock/unlock/push/pull events."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

AUDIT_LOG_FILENAME = "audit.log"


def get_audit_log_path(base_dir: Path | None = None) -> Path:
    """Return the path to the audit log file."""
    if base_dir is None:
        base_dir = Path.home() / ".envault"
    return base_dir / AUDIT_LOG_FILENAME


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(action: str, target: str, success: bool, base_dir: Path | None = None, note: str = "") -> None:
    """Append a single audit event to the log as a JSON line."""
    log_path = get_audit_log_path(base_dir)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": _now_iso(),
        "action": action,
        "target": target,
        "success": success,
    }
    if note:
        entry["note"] = note

    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_events(base_dir: Path | None = None) -> list[dict]:
    """Read all audit events from the log. Returns an empty list if none exist."""
    log_path = get_audit_log_path(base_dir)
    if not log_path.exists():
        return []

    events = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def clear_log(base_dir: Path | None = None) -> None:
    """Delete the audit log file if it exists."""
    log_path = get_audit_log_path(base_dir)
    if log_path.exists():
        log_path.unlink()
