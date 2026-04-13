"""CLI commands for vault sharing."""

from __future__ import annotations

from pathlib import Path

import click

from envault.keystore import keystore_exists, load_keystore
from envault.share import ShareError, export_shared_bundle, import_shared_bundle


@click.group(name="share")
def share_cli() -> None:
    """Share vault bundles with other users."""


@share_cli.command("export")
@click.argument("vault_name")
@click.option("--passphrase", prompt=True, hide_input=True, help="Your passphrase.")
@click.option(
    "--recipient-passphrase",
    prompt="Recipient passphrase",
    hide_input=True,
    confirmation_prompt=True,
    help="Passphrase for the recipient.",
)
@click.option("--out", "out_path", default=None, help="Output file path.")
@click.option("--base-dir", default=".", show_default=True)
def export_command(
    vault_name: str,
    passphrase: str,
    recipient_passphrase: str,
    out_path: str | None,
    base_dir: str,
) -> None:
    """Export VAULT_NAME as a bundle encrypted for a recipient."""
    base = Path(base_dir)
    if not keystore_exists(base):
        click.echo("No keystore found. Run `envault init` first.", err=True)
        raise SystemExit(1)
    try:
        fernet = load_keystore(base, passphrase)
        bundle = export_shared_bundle(base, vault_name, fernet, recipient_passphrase)
    except ShareError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    dest = Path(out_path) if out_path else Path(f"{vault_name}.envbundle")
    dest.write_bytes(bundle)
    click.echo(f"Bundle written to {dest}")


@share_cli.command("import")
@click.argument("bundle_file", type=click.Path(exists=True))
@click.option(
    "--passphrase",
    prompt="Your passphrase for this bundle",
    hide_input=True,
)
@click.option("--base-dir", default=".", show_default=True)
def import_command(bundle_file: str, passphrase: str, base_dir: str) -> None:
    """Import a shared bundle into the local vault directory."""
    base = Path(base_dir)
    bundle_bytes = Path(bundle_file).read_bytes()
    try:
        vault_name = import_shared_bundle(bundle_bytes, passphrase, base)
    except ShareError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    click.echo(f"Vault '{vault_name}' imported successfully.")
