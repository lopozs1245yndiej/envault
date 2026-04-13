"""Tests for the verify CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from envault.cli_verify import verify_cli
from envault.verify import VerifyResult, VerifyError


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_record_command_no_keystore(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(
        verify_cli, ["record", "default", "--base-dir", str(tmp_path)]
    )
    assert result.exit_code == 1
    assert "No keystore found" in result.output


def test_record_command_success(runner: CliRunner, tmp_path: Path) -> None:
    with (
        patch("envault.cli_verify.keystore_exists", return_value=True),
        patch("envault.cli_verify.record_checksum", return_value="abc123" + "0" * 58) as mock_rec,
    ):
        result = runner.invoke(
            verify_cli, ["record", "default", "--base-dir", str(tmp_path)]
        )
    assert result.exit_code == 0
    assert "Recorded checksum" in result.output
    mock_rec.assert_called_once()


def test_record_command_vault_missing(runner: CliRunner, tmp_path: Path) -> None:
    with (
        patch("envault.cli_verify.keystore_exists", return_value=True),
        patch("envault.cli_verify.record_checksum", side_effect=VerifyError("Vault 'x' not found.")),
    ):
        result = runner.invoke(
            verify_cli, ["record", "x", "--base-dir", str(tmp_path)]
        )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_check_command_ok(runner: CliRunner, tmp_path: Path) -> None:
    ok_result = VerifyResult("default", True, "abc", "abc")
    with (
        patch("envault.cli_verify.keystore_exists", return_value=True),
        patch("envault.cli_verify.verify_vault", return_value=ok_result),
    ):
        result = runner.invoke(
            verify_cli, ["check", "default", "--base-dir", str(tmp_path)]
        )
    assert result.exit_code == 0
    assert "integrity verified" in result.output


def test_check_command_tampered(runner: CliRunner, tmp_path: Path) -> None:
    bad_result = VerifyResult("default", False, "aaa", "bbb")
    with (
        patch("envault.cli_verify.keystore_exists", return_value=True),
        patch("envault.cli_verify.verify_vault", return_value=bad_result),
    ):
        result = runner.invoke(
            verify_cli, ["check", "default", "--base-dir", str(tmp_path)]
        )
    assert result.exit_code == 2
    assert "tampered" in result.output


def test_check_command_no_keystore(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(
        verify_cli, ["check", "default", "--base-dir", str(tmp_path)]
    )
    assert result.exit_code == 1
    assert "No keystore found" in result.output
