import os
import json
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

DEFAULT_VAULT_DIR = Path.home() / ".envault" / "vaults"


def get_vault_path(name: str, vault_dir: Path = DEFAULT_VAULT_DIR) -> Path:
    """Return the path to a named vault file."""
    return vault_dir / f"{name}.vault"


def vault_exists(name: str, vault_dir: Path = DEFAULT_VAULT_DIR) -> bool:
    """Check if a vault with the given name exists."""
    return get_vault_path(name, vault_dir).exists()


def encrypt_env(fernet: Fernet, env_path: Path) -> bytes:
    """Read a .env file and return its encrypted bytes."""
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found: {env_path}")
    plaintext = env_path.read_bytes()
    return fernet.encrypt(plaintext)


def decrypt_env(fernet: Fernet, ciphertext: bytes) -> str:
    """Decrypt vault ciphertext and return the plaintext string."""
    try:
        return fernet.decrypt(ciphertext).decode("utf-8")
    except InvalidToken:
        raise ValueError("Decryption failed: invalid key or corrupted vault.")


def save_vault(name: str, ciphertext: bytes, vault_dir: Path = DEFAULT_VAULT_DIR) -> Path:
    """Persist encrypted content to a vault file."""
    vault_dir.mkdir(parents=True, exist_ok=True)
    vault_path = get_vault_path(name, vault_dir)
    metadata = {
        "name": name,
        "ciphertext": ciphertext.decode("utf-8"),
    }
    vault_path.write_text(json.dumps(metadata, indent=2))
    return vault_path


def load_vault(name: str, vault_dir: Path = DEFAULT_VAULT_DIR) -> bytes:
    """Load a vault file and return the raw ciphertext bytes."""
    vault_path = get_vault_path(name, vault_dir)
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault '{name}' does not exist.")
    metadata = json.loads(vault_path.read_text())
    return metadata["ciphertext"].encode("utf-8")


def list_vaults(vault_dir: Path = DEFAULT_VAULT_DIR) -> list[str]:
    """Return a list of all vault names in the vault directory."""
    if not vault_dir.exists():
        return []
    return [p.stem for p in vault_dir.glob("*.vault")]
