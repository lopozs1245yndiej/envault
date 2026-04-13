"""Search for keys across vaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from cryptography.fernet import Fernet, InvalidToken

from envault.vault import get_vault_path, vault_exists, load_vault, decrypt_env


class SearchError(Exception):
    pass


@dataclass
class SearchMatch:
    vault_name: str
    key: str
    value: str


def _parse_env_bytes(data: bytes) -> dict[str, str]:
    """Parse raw env bytes into a key/value dict."""
    result: dict[str, str] = {}
    for line in data.decode().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


def search_vaults(
    base_dir: Path,
    fernet: Fernet,
    query: str,
    *,
    search_values: bool = False,
) -> List[SearchMatch]:
    """Search all vaults under *base_dir* for keys (or values) matching *query*.

    Args:
        base_dir: Root directory that contains vault files.
        fernet: Fernet instance used to decrypt vaults.
        query: Case-insensitive substring to search for.
        search_values: When True, also match against values.

    Returns:
        List of :class:`SearchMatch` objects.
    """
    if not query:
        raise SearchError("Search query must not be empty.")

    matches: List[SearchMatch] = []
    vault_dir = base_dir / "vaults"
    if not vault_dir.exists():
        return matches

    needle = query.lower()

    for vault_file in sorted(vault_dir.glob("*.vault")):
        vault_name = vault_file.stem
        try:
            encrypted = vault_file.read_bytes()
            raw = fernet.decrypt(encrypted)
        except (InvalidToken, Exception):
            continue

        pairs = _parse_env_bytes(raw)
        for key, value in pairs.items():
            key_hit = needle in key.lower()
            value_hit = search_values and needle in value.lower()
            if key_hit or value_hit:
                matches.append(SearchMatch(vault_name=vault_name, key=key, value=value))

    return matches
