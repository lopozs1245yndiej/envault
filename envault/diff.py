"""Diff utilities for comparing .env files against a vault."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from cryptography.fernet import Fernet

from envault.export import parse_env_bytes
from envault.vault import load_vault, vault_exists


@dataclass
class DiffEntry:
    key: str
    status: str  # 'added', 'removed', 'changed', 'unchanged'
    local_value: str | None = None
    vault_value: str | None = None


class DiffError(Exception):
    pass


def _parse_env_file(path: str) -> Dict[str, str]:
    """Read and parse a local .env file into a dict."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except FileNotFoundError:
        raise DiffError(f"Local env file not found: {path}")
    return parse_env_bytes(raw)


def diff_env(env_path: str, vault_name: str, fernet: Fernet, vault_dir: str) -> List[DiffEntry]:
    """Compare a local .env file against the decrypted vault contents.

    Returns a list of DiffEntry objects describing the differences.
    """
    if not vault_exists(vault_name, vault_dir):
        raise DiffError(f"Vault '{vault_name}' does not exist in {vault_dir}")

    local = _parse_env_file(env_path)
    vault_bytes = load_vault(vault_name, fernet, vault_dir)
    remote = parse_env_bytes(vault_bytes)

    all_keys = set(local) | set(remote)
    entries: List[DiffEntry] = []

    for key in sorted(all_keys):
        if key in local and key not in remote:
            entries.append(DiffEntry(key=key, status="added", local_value=local[key]))
        elif key in remote and key not in local:
            entries.append(DiffEntry(key=key, status="removed", vault_value=remote[key]))
        elif local[key] != remote[key]:
            entries.append(
                DiffEntry(key=key, status="changed", local_value=local[key], vault_value=remote[key])
            )
        else:
            entries.append(
                DiffEntry(key=key, status="unchanged", local_value=local[key], vault_value=remote[key])
            )

    ndef format_diff(entries: List[DiffEntry], show_values: bool = False) -> str:
    """Render diff entries as a human-readable string."""
    lines: List[str] = []
    symbols = {"added": "+", "removed": "-", "changed": "~", "unchanged": " "}

    for entry in entries:
        sym = symbols[entry.status]
        if show_values and entry.status == "changed":
            lines.append(f"{sym} {entry.key}  (local={entry.local_value!r} vault={entry.vault_value!r})")
        else:
            lines.append(f"{sym} {entry.key}")

    return "\n".join(lines) if lines else "(no keys found)"
