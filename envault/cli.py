"""Entry point for the envault CLI."""

import click
from pathlib import Path

from envault.keystore import (
    init_keystore,
    load_keystore,
    keystore_exists,
    DEFAULT_KEYSTORE_PATH,
)


@click.group()
def cli():
    """envault — encrypt and sync your .env files."""


@cli.command()
@click.option(
    "--passphrase",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Passphrase to protect your keystore.",
)
@click.option(
    "--keystore",
    default=str(DEFAULT_KEYSTORE_PATH),
    show_default=True,
    help="Path to the keystore file.",
)
def init(passphrase, keystore):
    """Initialize a new envault keystore."""
    path = Path(keystore)
    if keystore_exists(path):
        click.echo(f"Keystore already exists at {path}. Aborting.")
        raise SystemExit(1)
    try:
        init_keystore(passphrase, path=path)
        click.echo(f"✓ Keystore initialized at {path}")
    except Exception as e:
        click.echo(f"Error: {e}")
        raise SystemExit(1)


@cli.command()
@click.option("--passphrase", prompt=True, hide_input=True, help="Your keystore passphrase.")
@click.option("--keystore", default=str(DEFAULT_KEYSTORE_PATH), show_default=True)
def status(passphrase, keystore):
    """Check keystore status and verify passphrase."""
    path = Path(keystore)
    if not keystore_exists(path):
        click.echo("No keystore found. Run 'envault init' to get started.")
        raise SystemExit(1)
    try:
        load_keystore(passphrase, path=path)
        click.echo("✓ Keystore unlocked successfully.")
    except ValueError:
        click.echo("✗ Invalid passphrase.")
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
