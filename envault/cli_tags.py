"""CLI commands for managing vault tags."""

from __future__ import annotations

from pathlib import Path

import click

from envault.tags import (
    TagError,
    add_tag,
    clear_tags,
    find_by_tag,
    get_tags,
    remove_tag,
)

DEFAULT_BASE = Path.home() / ".envault"


@click.group("tags")
def tags_cli() -> None:
    """Manage tags on vaults."""


@tags_cli.command("add")
@click.argument("vault_name")
@click.argument("tag")
@click.option("--base-dir", default=str(DEFAULT_BASE), show_default=True)
def add_command(vault_name: str, tag: str, base_dir: str) -> None:
    """Add TAG to VAULT_NAME."""
    try:
        add_tag(Path(base_dir), vault_name, tag)
        click.echo(f"Tag '{tag}' added to '{vault_name}'.")
    except TagError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@tags_cli.command("remove")
@click.argument("vault_name")
@click.argument("tag")
@click.option("--base-dir", default=str(DEFAULT_BASE), show_default=True)
def remove_command(vault_name: str, tag: str, base_dir: str) -> None:
    """Remove TAG from VAULT_NAME."""
    try:
        remove_tag(Path(base_dir), vault_name, tag)
        click.echo(f"Tag '{tag}' removed from '{vault_name}'.")
    except TagError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@tags_cli.command("list")
@click.argument("vault_name")
@click.option("--base-dir", default=str(DEFAULT_BASE), show_default=True)
def list_command(vault_name: str, base_dir: str) -> None:
    """List all tags on VAULT_NAME."""
    tags = get_tags(Path(base_dir), vault_name)
    if tags:
        click.echo(", ".join(tags))
    else:
        click.echo(f"No tags found for '{vault_name}'.")


@tags_cli.command("find")
@click.argument("tag")
@click.option("--base-dir", default=str(DEFAULT_BASE), show_default=True)
def find_command(tag: str, base_dir: str) -> None:
    """Find all vaults carrying TAG."""
    vaults = find_by_tag(Path(base_dir), tag)
    if vaults:
        for name in vaults:
            click.echo(name)
    else:
        click.echo(f"No vaults found with tag '{tag}'.")
