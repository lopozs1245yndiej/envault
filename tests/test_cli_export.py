"""Tests for envault/cli_export.py"""

import json
import pytest
from click.testing import CliRunner
from cryptography.fernet import Fernet
from unittest.mock import patch, MagicMock

from envault.cli_export import export_cli
from envault.export import parse_env_bytes


SAMPLE_ENV = b"APP_ENV=production\nAPI_KEY=supersecret\n"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_fernet():
    f = MagicMock(spec=Fernet)
    f.decrypt.return_value = SAMPLE_ENV
    return f


def test_export_json_success(runner, mock_fernet, tmp_path):
    out_file = str(tmp_path / "out.json")
    with patch("envault.cli_export.keystore_exists", return_value=True), \
         patch("envault.cli_export.load_keystore", return_value=mock_fernet), \
         patch("envault.cli_export.export_to_json") as mock_export, \
         patch("envault.cli_export.log_event"):
        result = runner.invoke(export_cli, ["json", "myapp", out_file, "--passphrase", "secret"])
    assert result.exit_code == 0
    assert "Exported 'myapp'" in result.output
    mock_export.assert_called_once()


def test_export_dotenv_success(runner, mock_fernet, tmp_path):
    out_file = str(tmp_path / "out.env")
    with patch("envault.cli_export.keystore_exists", return_value=True), \
         patch("envault.cli_export.load_keystore", return_value=mock_fernet), \
         patch("envault.cli_export.export_to_dotenv") as mock_export, \
         patch("envault.cli_export.log_event"):
        result = runner.invoke(export_cli, ["dotenv", "myapp", out_file, "--passphrase", "secret"])
    assert result.exit_code == 0
    mock_export.assert_called_once()


def test_export_shell_success(runner, mock_fernet):
    with patch("envault.cli_export.keystore_exists", return_value=True), \
         patch("envault.cli_export.load_keystore", return_value=mock_fernet), \
         patch("envault.cli_export.export_to_shell", return_value='export APP_ENV="production"'), \
         patch("envault.cli_export.log_event"):
        result = runner.invoke(export_cli, ["shell", "myapp", "--passphrase", "secret"])
    assert result.exit_code == 0
    assert "export APP_ENV" in result.output


def test_export_fails_without_keystore(runner):
    with patch("envault.cli_export.keystore_exists", return_value=False):
        result = runner.invoke(export_cli, ["json", "myapp", "out.json", "--passphrase", "x"])
    assert result.exit_code != 0
    assert "not initialized" in result.output


def test_export_json_handles_error(runner, tmp_path):
    out_file = str(tmp_path / "out.json")
    with patch("envault.cli_export.keystore_exists", return_value=True), \
         patch("envault.cli_export.load_keystore", side_effect=ValueError("bad passphrase")):
        result = runner.invoke(export_cli, ["json", "myapp", out_file, "--passphrase", "wrong"])
    assert result.exit_code != 0
    assert "Export failed" in result.output
