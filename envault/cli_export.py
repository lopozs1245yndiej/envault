"""CLI commands for exporting vault contents."""

import click
from pathlib import Path

from envault.keystore import load_keystore, keystore_exists
from envault.export import export_to_json, export_to_dotenv, export_to_shell
from envault.audit import log_event


@click.group()
def export_cli():
    """Export decrypted vault contents."""
    pass


@export_cli.command("json")
@click.argument("vault_name")
@click.argument("output", type=click.Path())
@click.password_option("--passphrase", prompt="Passphrase", confirmation_prompt=False)
def export_json(vault_name: str, output: str, passphrase: str):
    """Export vault to a JSON file."""
    if not keystore_exists():
        click.echo("Keystore not initialized. Run `envault init` first.")
        raise SystemExit(1)
    try:
        fernet = load_keystore(passphrase)
        export_to_json(fernet, vault_name, Path(output))
        log_event("export_json", vault_name, note=f"output={output}")
        click.echo(f"Exported '{vault_name}' to {output}")
    except Exception as e:
        click.echo(f"Export failed: {e}")
        raise SystemExit(1)


@export_cli.command("dotenv")
@click.argument("vault_name")
@click.argument("output", type=click.Path())
@click.password_option("--passphrase", prompt="Passphrase", confirmation_prompt=False)
def export_dotenv(vault_name: str, output: str, passphrase: str):
    """Export vault to a plain .env file."""
    if not keystore_exists():
        click.echo("Keystore not initialized. Run `envault init` first.")
        raise SystemExit(1)
    try:
        fernet = load_keystore(passphrase)
        export_to_dotenv(fernet, vault_name, Path(output))
        log_event("export_dotenv", vault_name, note=f"output={output}")
        click.echo(f"Exported '{vault_name}' to {output}")
    except Exception as e:
        click.echo(f"Export failed: {e}")
        raise SystemExit(1)


@export_cli.command("shell")
@click.argument("vault_name")
@click.password_option("--passphrase", prompt="Passphrase", confirmation_prompt=False)
def export_shell(vault_name: str, passphrase: str):
    """Print shell export statements for vault contents."""
    if not keystore_exists():
        click.echo("Keystore not initialized. Run `envault init` first.")
        raise SystemExit(1)
    try:
        fernet = load_keystore(passphrase)
        output = export_to_shell(fernet, vault_name)
        log_event("export_shell", vault_name)
        click.echo(output)
    except Exception as e:
        click.echo(f"Export failed: {e}")
        raise SystemExit(1)
