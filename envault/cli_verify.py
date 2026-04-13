"""CLI commands for vault integrity verification."""

from __future__ import annotations

from pathlib import Path

import click

from envault.keystore import keystore_exists
from envault.verify import VerifyError, record_checksum, verify_vault


@click.group("verify")
def verify_cli() -> None:
    """Vault integrity verification commands."""


@verify_cli.command("record")
@click.argument("vault_name")
@click.option("--base-dir", default=".", show_default=True)
def record_command(vault_name: str, base_dir: str) -> None:
    """Record a checksum for VAULT_NAME."""
    base = Path(base_dir)
    if not keystore_exists(base):
        click.echo("No keystore found. Run 'envault init' first.", err=True)
        raise SystemExit(1)
    try:
        digest = record_checksum(base, vault_name)
        click.echo(f"Recorded checksum for '{vault_name}': {digest[:12]}...")
    except VerifyError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@verify_cli.command("check")
@click.argument("vault_name")
@click.option("--base-dir", default=".", show_default=True)
def check_command(vault_name: str, base_dir: str) -> None:
    """Check integrity of VAULT_NAME against its recorded checksum."""
    base = Path(base_dir)
    if not keystore_exists(base):
        click.echo("No keystore found. Run 'envault init' first.", err=True)
        raise SystemExit(1)
    try:
        result = verify_vault(base, vault_name)
    except VerifyError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)

    if result.ok:
        click.echo(f"✓ '{vault_name}' integrity verified.")
    else:
        click.echo(
            f"✗ '{vault_name}' has been tampered with!",
            err=True,
        )
        click.echo(f"  expected: {result.expected}", err=True)
        click.echo(f"  actual  : {result.actual}", err=True)
        raise SystemExit(2)
