"""Passphrase rotation for envault keystores and vaults."""

from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

from envault.keystore import load_keystore, init_keystore, _derive_key, keystore_exists
from envault.vault import vault_exists, get_vault_path, load_vault, save_vault
from envault.audit import log_event


class RotationError(Exception):
    """Raised when passphrase rotation fails."""
    pass


def rotate_passphrase(
    base_dir: Path,
    old_passphrase: str,
    new_passphrase: str,
    vault_names: list[str] | None = None,
) -> list[str]:
    """Rotate the keystore passphrase and re-encrypt all specified vaults.

    Args:
        base_dir: Root directory containing keystore and vaults.
        old_passphrase: Current passphrase used to unlock the keystore.
        new_passphrase: New passphrase to protect the keystore.
        vault_names: List of vault names to re-encrypt. If None, skips vault rotation.

    Returns:
        List of vault names that were successfully re-encrypted.

    Raises:
        RotationError: If the keystore doesn't exist or old passphrase is wrong.
    """
    if not keystore_exists(base_dir):
        raise RotationError("No keystore found. Run 'envault init' first.")

    try:
        old_fernet = load_keystore(base_dir, old_passphrase)
    except Exception as exc:
        raise RotationError(f"Failed to unlock keystore with old passphrase: {exc}") from exc

    rotated = []

    if vault_names:
        # Decrypt all vaults with old key before changing anything
        vault_plaintexts: dict[str, bytes] = {}
        for name in vault_names:
            if not vault_exists(base_dir, name):
                raise RotationError(f"Vault '{name}' not found — aborting rotation.")
            try:
                encrypted = load_vault(base_dir, name)
                vault_plaintexts[name] = old_fernet.decrypt(encrypted)
            except InvalidToken as exc:
                raise RotationError(
                    f"Could not decrypt vault '{name}' with old passphrase."
                ) from exc

    # Re-initialise keystore with new passphrase (overwrites existing)
    keystore_path = base_dir / ".envault" / "keystore.enc"
    keystore_path.unlink(missing_ok=True)
    new_fernet = init_keystore(base_dir, new_passphrase)

    if vault_names:
        for name, plaintext in vault_plaintexts.items():
            re_encrypted = new_fernet.encrypt(plaintext)
            save_vault(base_dir, name, re_encrypted)
            rotated.append(name)

    log_event(base_dir, "rotate", note=f"rotated passphrase, vaults={rotated}")
    return rotated
