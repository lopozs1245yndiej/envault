"""Export decrypted .env files to various formats."""

import json
from pathlib import Path
from cryptography.fernet import Fernet

from envault.vault import get_vault_path, load_vault, decrypt_env


def parse_env_bytes(env_bytes: bytes) -> dict:
    """Parse raw .env bytes into a key-value dictionary."""
    result = {}
    for line in env_bytes.decode().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def export_to_json(fernet: Fernet, vault_name: str, output_path: Path) -> None:
    """Decrypt vault and export its contents as a JSON file."""
    vault_path = get_vault_path(vault_name)
    env_bytes = decrypt_env(fernet, vault_path)
    data = parse_env_bytes(env_bytes)
    output_path.write_text(json.dumps(data, indent=2))


def export_to_dotenv(fernet: Fernet, vault_name: str, output_path: Path) -> None:
    """Decrypt vault and write it back as a plain .env file."""
    vault_path = get_vault_path(vault_name)
    env_bytes = decrypt_env(fernet, vault_path)
    output_path.write_bytes(env_bytes)


def export_to_shell(fernet: Fernet, vault_name: str) -> str:
    """Return a shell-exportable string of environment variable assignments."""
    vault_path = get_vault_path(vault_name)
    env_bytes = decrypt_env(fernet, vault_path)
    data = parse_env_bytes(env_bytes)
    lines = [f'export {k}="{v}"' for k, v in data.items()]
    return "\n".join(lines)
