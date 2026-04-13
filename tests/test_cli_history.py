"""Tests for CLI history commands."""

import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from envault.cli_history import history_cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_snapshot_command_no_keystore(runner, base_dir):
    result = runner.invoke(
        history_cli, ["snapshot", "myenv", "--dir", str(base_dir)]
    )
    assert result.exit_code != 0
    assert "keystore not initialised" in result.output


def test_snapshot_command_no_vault(runner, base_dir):
    with patch("envault.cli_history.keystore_exists", return_value=True), \
         patch("envault.cli_history.vault_exists", return_value=False):
        result = runner.invoke(
            history_cli, ["snapshot", "myenv", "--dir", str(base_dir)]
        )
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_snapshot_command_success(runner, base_dir):
    mock_meta = MagicMock(index=0, timestamp="2024-01-01T00:00:00+00:00")
    with patch("envault.cli_history.keystore_exists", return_value=True), \
         patch("envault.cli_history.vault_exists", return_value=True), \
         patch("envault.cli_history.save_snapshot", return_value=mock_meta) as mock_snap:
        result = runner.invoke(
            history_cli, ["snapshot", "myenv", "--note", "v1", "--dir", str(base_dir)]
        )
    assert result.exit_code == 0
    assert "Snapshot 0 saved" in result.output
    mock_snap.assert_called_once()


def test_list_command_empty(runner, base_dir):
    with patch("envault.cli_history.list_snapshots", return_value=[]):
        result = runner.invoke(
            history_cli, ["list", "myenv", "--dir", str(base_dir)]
        )
    assert result.exit_code == 0
    assert "No snapshots" in result.output


def test_list_command_shows_entries(runner, base_dir):
    snap = MagicMock(index=2, timestamp="2024-06-01T12:00:00+00:00", note="after rotate")
    with patch("envault.cli_history.list_snapshots", return_value=[snap]):
        result = runner.invoke(
            history_cli, ["list", "myenv", "--dir", str(base_dir)]
        )
    assert result.exit_code == 0
    assert "[2]" in result.output
    assert "after rotate" in result.output


def test_restore_command_success(runner, base_dir):
    with patch("envault.cli_history.keystore_exists", return_value=True), \
         patch("envault.cli_history.restore_snapshot") as mock_restore:
        result = runner.invoke(
            history_cli, ["restore", "myenv", "1", "--dir", str(base_dir)]
        )
    assert result.exit_code == 0
    assert "restored from snapshot 1" in result.output
    mock_restore.assert_called_once()


def test_restore_command_not_found(runner, base_dir):
    with patch("envault.cli_history.keystore_exists", return_value=True), \
         patch("envault.cli_history.restore_snapshot", side_effect=FileNotFoundError("Snapshot 99 not found")):
        result = runner.invoke(
            history_cli, ["restore", "myenv", "99", "--dir", str(base_dir)]
        )
    assert result.exit_code != 0
    assert "Snapshot 99 not found" in result.output
