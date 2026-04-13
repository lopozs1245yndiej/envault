# envault

> A CLI tool for encrypting and syncing `.env` files across machines using a passphrase-protected local keystore.

---

## Installation

```bash
pip install envault
```

Or install from source:

```bash
pip install git+https://github.com/yourname/envault.git
```

---

## Usage

**Initialize a new vault and add your `.env` file:**

```bash
envault init
envault lock .env --name myproject
```

**Unlock and restore a `.env` file on another machine:**

```bash
envault unlock myproject --output .env
```

**List all stored secrets:**

```bash
envault list
```

You'll be prompted for your passphrase on first use. The encrypted keystore is stored locally at `~/.envault/vault.enc`.

---

## How It Works

`envault` encrypts your `.env` files using AES-256 encryption derived from your passphrase via PBKDF2. The encrypted vault lives on your local machine and can be safely copied or synced across machines manually or via a tool like Dropbox or rsync.

---

## Requirements

- Python 3.8+
- `cryptography`
- `click`

---

## License

MIT © 2024 [yourname](https://github.com/yourname)