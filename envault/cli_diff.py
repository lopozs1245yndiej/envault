"""CLI commands for diffing a local .env against the vault."""

import os

import click

from envault.diff import DiffError, diff_env, format_diff
from envault.keystore import load_keystore, keystore_exists
from envault.vault import get_vault_path

DEFAULT_KEYSTORE_DIR = os.path.expanduser("~/.envault")
DEFAULT_VAULT_DIR = os.path.join(DEFAULT_KEYSTORE_DIR, "vaults")


@click.group()
def diff_cli():
    """Diff commands for envault."""


@diff_cli.command("diff")
@click.argument("vault_name")
@click.option("--env-file", default=".env", show_default=True, help="Path to local .env file.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Keystore passphrase.")
@click.option("--show-values", is_flag=True, default=False, help="Show changed values in output.")
@click.option("--vault-dir", default=DEFAULT_VAULT_DIR, hidden=True)
@click.option("--keystore-dir", default=DEFAULT_KEYSTORE_DIR, hidden=True)
def diff_command(vault_name: str, env_file: str, passphrase: str, show_values: bool, vault_dir: str, keystore_dir: str):
    """Show differences between a local .env file and the vault."""
    if not keystore_exists(keystore_dir):
        click.echo("error: keystore not initialised. Run `envault init` first.", err=True)
        raise SystemExit(1)

    try:
        fernet = load_keystore(passphrase, keystore_dir)
    except Exception:
        click.echo("error: wrong passphrase or corrupted keystore.", err=True)
        raise SystemExit(1)

    try:
        entries = diff_env(env_file, vault_name, fernet, vault_dir)
    except DiffError as exc:
        click.echo(f"error: {exc}", err=True)
        raise SystemExit(1)

    added = sum(1 for e in entries if e.status == "added")
    removed = sum(1 for e in entries if e.status == "removed")
    changed = sum(1 for e in entries if e.status == "changed")

    click.echo(format_diff(entries, show_values=show_values))
    click.echo(f"\nsummary: +{added} added  -{removed} removed  ~{changed} changed")
