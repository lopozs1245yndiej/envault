"""Tests for the keystore module."""

import pytest
from pathlib import Path
from cryptography.fernet import Fernet

from envault.keystore import init_keystore, load_keystore, keystore_exists


@pytest.fixture
def tmp_keystore(tmp_path):
    return tmp_path / "keystore.json"


def test_init_creates_keystore(tmp_keystore):
    init_keystore("my-secret", path=tmp_keystore)
    assert tmp_keystore.exists()


def test_init_raises_if_already_exists(tmp_keystore):
    init_keystore("my-secret", path=tmp_keystore)
    with pytest.raises(FileExistsError):
        init_keystore("my-secret", path=tmp_keystore)


def test_load_returns_fernet_instance(tmp_keystore):
    init_keystore("correct-passphrase", path=tmp_keystore)
    fernet = load_keystore("correct-passphrase", path=tmp_keystore)
    assert isinstance(fernet, Fernet)


def test_load_raises_on_wrong_passphrase(tmp_keystore):
    init_keystore("correct-passphrase", path=tmp_keystore)
    with pytest.raises(ValueError, match="Invalid passphrase"):
        load_keystore("wrong-passphrase", path=tmp_keystore)


def test_load_raises_if_no_keystore(tmp_keystore):
    with pytest.raises(FileNotFoundError):
        load_keystore("any-passphrase", path=tmp_keystore)


def test_keystore_exists(tmp_keystore):
    assert not keystore_exists(path=tmp_keystore)
    init_keystore("pass", path=tmp_keystore)
    assert keystore_exists(path=tmp_keystore)


def test_fernet_can_roundtrip(tmp_keystore):
    init_keystore("roundtrip-pass", path=tmp_keystore)
    fernet = load_keystore("roundtrip-pass", path=tmp_keystore)
    plaintext = b"SECRET=hunter2"
    assert fernet.decrypt(fernet.encrypt(plaintext)) == plaintext
