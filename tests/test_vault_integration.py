import pytest
from pathlib import Path
from cryptography.fernet import Fernet
from envault.vault import encrypt_env, decrypt_env, save_vault, load_vault, list_vaults


@pytest.fixture
def vault_dir(tmp_path):
    return tmp_path / "vaults"


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("APP_ENV=production\nDATABASE_URL=postgres://localhost/mydb\nSECRET_KEY=supersecret\n")
    return f


@pytest.fixture
def fernet():
    return Fernet(Fernet.generate_key())


def test_full_lock_unlock_cycle(fernet, env_file, vault_dir, tmp_path):
    """Full round-trip: encrypt, save, load, decrypt."""
    original_content = env_file.read_text()

    ciphertext = encrypt_env(fernet, env_file)
    save_vault("integration", ciphertext, vault_dir)

    loaded_ciphertext = load_vault("integration", vault_dir)
    recovered = decrypt_env(fernet, loaded_ciphertext)

    assert recovered == original_content


def test_multiple_vaults_isolated(fernet, tmp_path, vault_dir):
    """Multiple vaults don't interfere with each other."""
    env_a = tmp_path / "a.env"
    env_b = tmp_path / "b.env"
    env_a.write_text("SERVICE=alpha\n")
    env_b.write_text("SERVICE=beta\n")

    save_vault("proj-a", encrypt_env(fernet, env_a), vault_dir)
    save_vault("proj-b", encrypt_env(fernet, env_b), vault_dir)

    recovered_a = decrypt_env(fernet, load_vault("proj-a", vault_dir))
    recovered_b = decrypt_env(fernet, load_vault("proj-b", vault_dir))

    assert "alpha" in recovered_a
    assert "beta" in recovered_b
    assert "alpha" not in recovered_b


def test_list_vaults_after_saves(fernet, env_file, vault_dir):
    for name in ["dev", "staging", "prod"]:
        save_vault(name, encrypt_env(fernet, env_file), vault_dir)
    names = sorted(list_vaults(vault_dir))
    assert names == ["dev", "prod", "staging"]


def test_overwrite_vault(fernet, tmp_path, vault_dir):
    """Saving to the same vault name overwrites it."""
    env1 = tmp_path / "v1.env"
    env2 = tmp_path / "v2.env"
    env1.write_text("VERSION=1\n")
    env2.write_text("VERSION=2\n")

    save_vault("versioned", encrypt_env(fernet, env1), vault_dir)
    save_vault("versioned", encrypt_env(fernet, env2), vault_dir)

    recovered = decrypt_env(fernet, load_vault("versioned", vault_dir))
    assert "VERSION=2" in recovered
