"""CLI tests for envault share commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from cryptography.fernet import Fernet

from envault.cli_share import share_cli


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def mock_fernet() -> Fernet:
    return Fernet(Fernet.generate_key())


def test_export_command_no_keystore(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(
        share_cli,
        ["export", "myapp", "--passphrase", "pw", "--recipient-passphrase", "rp",
         "--base-dir", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "No keystore" in result.output


def test_export_command_success(runner: CliRunner, tmp_path: Path, mock_fernet: Fernet) -> None:
    bundle_bytes = json.dumps({"vault": "myapp", "salt": "aa", "ciphertext": "xx"}).encode()
    with (
        patch("envault.cli_share.keystore_exists", return_value=True),
        patch("envault.cli_share.load_keystore", return_value=mock_fernet),
        patch("envault.cli_share.export_shared_bundle", return_value=bundle_bytes),
    ):
        out_file = tmp_path / "myapp.envbundle"
        result = runner.invoke(
            share_cli,
            ["export", "myapp", "--passphrase", "pw", "--recipient-passphrase", "rp",
             "--out", str(out_file), "--base-dir", str(tmp_path)],
        )
    assert result.exit_code == 0
    assert "Bundle written" in result.output


def test_import_command_success(runner: CliRunner, tmp_path: Path) -> None:
    bundle_file = tmp_path / "myapp.envbundle"
    bundle_file.write_bytes(b"dummy")
    with patch("envault.cli_share.import_shared_bundle", return_value="myapp"):
        result = runner.invoke(
            share_cli,
            ["import", str(bundle_file), "--passphrase", "pw",
             "--base-dir", str(tmp_path)],
        )
    assert result.exit_code == 0
    assert "imported successfully" in result.output


def test_import_command_wrong_passphrase(runner: CliRunner, tmp_path: Path) -> None:
    from envault.share import ShareError
    bundle_file = tmp_path / "myapp.envbundle"
    bundle_file.write_bytes(b"dummy")
    with patch("envault.cli_share.import_shared_bundle", side_effect=ShareError("Wrong passphrase")):
        result = runner.invoke(
            share_cli,
            ["import", str(bundle_file), "--passphrase", "bad",
             "--base-dir", str(tmp_path)],
        )
    assert result.exit_code != 0
    assert "Wrong passphrase" in result.output
