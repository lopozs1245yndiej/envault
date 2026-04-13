import pytest
from pathlib import Path
from cryptography.fernet import Fernet
from envault.vault import (
    encrypt_env,
    decrypt_env,
    save_vault,
    load_vault,
    vault_exists,
    list_vaults,
)


@pytest.fixture
def fernet_key():
    return Fernet(Fernet.generate_key())


@pytest.fixture
def sample_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc123\n")
    return env_file


@pytest.fixture
def vault_dir(tmp_path):
    return tmp_path / "vaults"


def test_encrypt_env_returns_bytes(fernet_key, sample_env_file):
    ciphertext = encrypt_env(fernet_key, sample_env_file)
    assert isinstance(ciphertext, bytes)
    assert ciphertext != sample_env_file.read_bytes()


def test_encrypt_env_raises_if_file_missing(fernet_key, tmp_path):
    with pytest.raises(FileNotFoundError):
        encrypt_env(fernet_key, tmp_path / "nonexistent.env")


def test_decrypt_env_roundtrip(fernet_key, sample_env_file):
    ciphertext = encrypt_env(fernet_key, sample_env_file)
    plaintext = decrypt_env(fernet_key, ciphertext)
    assert "DB_HOST=localhost" in plaintext
    assert "SECRET=abc123" in plaintext


def test_decrypt_env_raises_on_wrong_key(fernet_key, sample_env_file):
    ciphertext = encrypt_env(fernet_key, sample_env_file)
    wrong_fernet = Fernet(Fernet.generate_key())
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt_env(wrong_fernet, ciphertext)


def test_save_and_load_vault(fernet_key, sample_env_file, vault_dir):
    ciphertext = encrypt_env(fernet_key, sample_env_file)
    save_vault("myproject", ciphertext, vault_dir)
    loaded = load_vault("myproject", vault_dir)
    assert loaded == ciphertext


def test_vault_exists(fernet_key, sample_env_file, vault_dir):
    assert not vault_exists("myproject", vault_dir)
    ciphertext = encrypt_env(fernet_key, sample_env_file)
    save_vault("myproject", ciphertext, vault_dir)
    assert vault_exists("myproject", vault_dir)


def test_load_vault_raises_if_missing(vault_dir):
    with pytest.raises(FileNotFoundError):
        load_vault("ghost", vault_dir)


def test_list_vaults(fernet_key, sample_env_file, vault_dir):
    assert list_vaults(vault_dir) == []
    ciphertext = encrypt_env(fernet_key, sample_env_file)
    save_vault("alpha", ciphertext, vault_dir)
    save_vault("beta", ciphertext, vault_dir)
    names = sorted(list_vaults(vault_dir))
    assert names == ["alpha", "beta"]
