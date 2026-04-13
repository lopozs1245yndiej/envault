import click
from pathlib import Path
from envault.keystore import init_keystore, load_keystore, keystore_exists
from envault.vault import (
    encrypt_env,
    decrypt_env,
    save_vault,
    load_vault,
    vault_exists,
    list_vaults,
)


@click.group()
def cli():
    """envault — encrypt and sync .env files with a passphrase-protected keystore."""
    pass


@cli.command()
@click.option("--passphrase", prompt=True, hide_input=True, confirmation_prompt=True)
def init(passphrase):
    """Initialize a new envault keystore."""
    try:
        path = init_keystore(passphrase)
        click.echo(f"✓ Keystore initialized at {path}")
    except FileExistsError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(1)


@cli.command()
def status():
    """Show keystore and vault status."""
    if not keystore_exists():
        click.echo("✗ No keystore found. Run `envault init` to get started.")
        return
    click.echo("✓ Keystore found.")
    names = list_vaults()
    if names:
        click.echo(f"  Vaults ({len(names)}): {', '.join(sorted(names))}")
    else:
        click.echo("  No vaults yet. Use `envault lock` to create one.")


@cli.command()
@click.argument("name")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path), default=Path(".env"))
@click.option("--passphrase", prompt=True, hide_input=True)
def lock(name, env_file, passphrase):
    """Encrypt an .env file into a named vault."""
    try:
        fernet = load_keystore(passphrase)
    except ValueError as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(1)

    ciphertext = encrypt_env(fernet, env_file)
    path = save_vault(name, ciphertext)
    click.echo(f"✓ Locked '{env_file}' into vault '{name}' at {path}")


@cli.command()
@click.argument("name")
@click.argument("output", type=click.Path(path_type=Path), default=Path(".env"))
@click.option("--passphrase", prompt=True, hide_input=True)
@click.option("--force", is_flag=True, help="Overwrite output file if it exists.")
def unlock(name, output, passphrase, force):
    """Decrypt a vault back into an .env file."""
    if output.exists() and not force:
        click.echo(f"✗ '{output}' already exists. Use --force to overwrite.", err=True)
        raise SystemExit(1)
    try:
        fernet = load_keystore(passphrase)
        ciphertext = load_vault(name)
        plaintext = decrypt_env(fernet, ciphertext)
    except (ValueError, FileNotFoundError) as e:
        click.echo(f"✗ {e}", err=True)
        raise SystemExit(1)

    output.write_text(plaintext)
    click.echo(f"✓ Unlocked vault '{name}' into '{output}'")
