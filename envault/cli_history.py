"""CLI commands for vault snapshot history."""

from pathlib import Path

import click

from envault.history import save_snapshot, list_snapshots, restore_snapshot
from envault.keystore import keystore_exists
from envault.vault import get_vault_path, vault_exists


@click.group(name="history")
def history_cli():
    """Manage vault snapshot history."""


@history_cli.command(name="snapshot")
@click.argument("vault_name")
@click.option("--note", default="", help="Optional note for this snapshot.")
@click.option("--dir", "base_dir", default=".", show_default=True, help="Base directory.")
def snapshot_command(vault_name: str, note: str, base_dir: str):
    """Save a snapshot of the current vault."""
    base = Path(base_dir)
    if not keystore_exists(base):
        click.echo("Error: keystore not initialised. Run `envault init` first.", err=True)
        raise SystemExit(1)

    vault_path = get_vault_path(base, vault_name)
    if not vault_exists(base, vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)

    meta = save_snapshot(base, vault_path, vault_name, note=note)
    click.echo(f"Snapshot {meta.index} saved for '{vault_name}' at {meta.timestamp}.")


@history_cli.command(name="list")
@click.argument("vault_name")
@click.option("--dir", "base_dir", default=".", show_default=True, help="Base directory.")
def list_command(vault_name: str, base_dir: str):
    """List all snapshots for a vault."""
    base = Path(base_dir)
    snapshots = list_snapshots(base, vault_name)
    if not snapshots:
        click.echo(f"No snapshots found for '{vault_name}'.")
        return
    for s in snapshots:
        note_part = f"  # {s.note}" if s.note else ""
        click.echo(f"[{s.index}] {s.timestamp}{note_part}")


@history_cli.command(name="restore")
@click.argument("vault_name")
@click.argument("index", type=int)
@click.option("--dir", "base_dir", default=".", show_default=True, help="Base directory.")
def restore_command(vault_name: str, index: int, base_dir: str):
    """Restore a vault snapshot by index."""
    base = Path(base_dir)
    if not keystore_exists(base):
        click.echo("Error: keystore not initialised.", err=True)
        raise SystemExit(1)

    dest = get_vault_path(base, vault_name)
    try:
        restore_snapshot(base, vault_name, index, dest)
        click.echo(f"Vault '{vault_name}' restored from snapshot {index}.")
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
