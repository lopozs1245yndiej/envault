import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet
from envault.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_fernet():
    key = Fernet.generate_key()
    return Fernet(key)


def test_lock_command_success(runner, tmp_path, mock_fernet):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=value\n")
    vault_dir = tmp_path / "vaults"

    with patch("envault.cli.load_keystore", return_value=mock_fernet), \
         patch("envault.cli.save_vault", return_value=vault_dir / "test.vault") as mock_save:
        result = runner.invoke(cli, ["lock", "test", str(env_file)], input="passphrase\n")

    assert result.exit_code == 0
    assert "Locked" in result.output
    mock_save.assert_called_once()


def test_lock_command_wrong_passphrase(runner, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=value\n")

    with patch("envault.cli.load_keystore", side_effect=ValueError("Wrong passphrase")):
        result = runner.invoke(cli, ["lock", "test", str(env_file)], input="wrong\n")

    assert result.exit_code == 1
    assert "Wrong passphrase" in result.output


def test_unlock_command_success(runner, tmp_path, mock_fernet):
    env_content = "DB=postgres\n"
    ciphertext = mock_fernet.encrypt(env_content.encode())
    output_file = tmp_path / "out.env"

    with patch("envault.cli.load_keystore", return_value=mock_fernet), \
         patch("envault.cli.load_vault", return_value=ciphertext):
        result = runner.invoke(
            cli, ["unlock", "myproject", str(output_file)], input="passphrase\n"
        )

    assert result.exit_code == 0
    assert "Unlocked" in result.output
    assert output_file.read_text() == env_content


def test_unlock_refuses_overwrite_without_force(runner, tmp_path, mock_fernet):
    existing = tmp_path / ".env"
    existing.write_text("OLD=data\n")

    with patch("envault.cli.load_keystore", return_value=mock_fernet):
        result = runner.invoke(
            cli, ["unlock", "myproject", str(existing)], input="passphrase\n"
        )

    assert result.exit_code == 1
    assert "already exists" in result.output


def test_status_shows_vaults(runner):
    with patch("envault.cli.keystore_exists", return_value=True), \
         patch("envault.cli.list_vaults", return_value=["alpha", "beta"]):
        result = runner.invoke(cli, ["status"])

    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "beta" in result.output
