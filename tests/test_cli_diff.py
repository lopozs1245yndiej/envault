"""CLI tests for the diff command."""

import os
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from envault.cli_diff import diff_cli
from envault.diff import DiffEntry, DiffError


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_fernet():
    return MagicMock()


def _make_entries():
    return [
        DiffEntry(key="FOO", status="added", local_value="bar"),
        DiffEntry(key="BAZ", status="unchanged", local_value="qux", vault_value="qux"),
    ]


def test_diff_command_success(runner, mock_fernet):
    with patch("envault.cli_diff.keystore_exists", return_value=True), \
         patch("envault.cli_diff.load_keystore", return_value=mock_fernet), \
         patch("envault.cli_diff.diff_env", return_value=_make_entries()):
        result = runner.invoke(diff_cli, ["diff", "myapp", "--passphrase", "secret"])
    assert result.exit_code == 0
    assert "+" in result.output
    assert "summary" in result.output


def test_diff_command_no_keystore(runner):
    with patch("envault.cli_diff.keystore_exists", return_value=False):
        result = runner.invoke(diff_cli, ["diff", "myapp", "--passphrase", "secret"])
    assert result.exit_code != 0
    assert "not initialised" in result.output


def test_diff_command_wrong_passphrase(runner):
    with patch("envault.cli_diff.keystore_exists", return_value=True), \
         patch("envault.cli_diff.load_keystore", side_effect=Exception("bad passphrase")):
        result = runner.invoke(diff_cli, ["diff", "myapp", "--passphrase", "wrong"])
    assert result.exit_code != 0
    assert "wrong passphrase" in result.output


def test_diff_command_vault_missing(runner, mock_fernet):
    with patch("envault.cli_diff.keystore_exists", return_value=True), \
         patch("envault.cli_diff.load_keystore", return_value=mock_fernet), \
         patch("envault.cli_diff.diff_env", side_effect=DiffError("Vault 'x' does not exist")):
        result = runner.invoke(diff_cli, ["diff", "x", "--passphrase", "secret"])
    assert result.exit_code != 0
    assert "error" in result.output


def test_diff_command_show_values(runner, mock_fernet):
    entries = [DiffEntry(key="TOKEN", status="changed", local_value="new", vault_value="old")]
    with patch("envault.cli_diff.keystore_exists", return_value=True), \
         patch("envault.cli_diff.load_keystore", return_value=mock_fernet), \
         patch("envault.cli_diff.diff_env", return_value=entries):
        result = runner.invoke(diff_cli, ["diff", "myapp", "--passphrase", "secret", "--show-values"])
    assert result.exit_code == 0
    assert "new" in result.output
    assert "old" in result.output
