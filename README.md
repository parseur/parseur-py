<!-- mcp-name: io.github.parseur/parseur-py -->

# 🤖🧙parseur-py

**parseur-py** is a modern Python client for the [Parseur](https://parseur.com) API.

It lets you **manage mailboxes, documents, uploads, and webhooks** programmatically or from the command line.

Built to help you automate document parsing at scale, parseur-py makes integrating with Parseur fast, easy, and Pythonic.

[![GitHub Repo](https://img.shields.io/badge/GitHub-parseur--py-blue?logo=github)](https://github.com/parseur/parseur-py)
[![PyPI version](https://badge.fury.io/py/parseur-py.svg)](https://badge.fury.io/py/parseur-py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Read the Docs](https://readthedocs.org/projects/parseur-py/badge/?version=latest)](https://parseur-py.readthedocs.io/en/latest/?badge=latest)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/parseur-py?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=users)](https://pepy.tech/projects/parseur-py)

---

## ✨ Features

✅ List, search, and sort mailboxes  
✅ Get mailbox details and schema  
✅ List, search, filter, and sort documents  
✅ Upload documents by file or email content  
✅ Reprocess, skip, copy, or delete documents  
✅ Manage custom webhooks for real-time events  
✅ Listen to events in real time with a temporary webhook & tunnel  
✅ Fully-featured **Command Line Interface (CLI)**  
✅ Built-in **MCP server** to drive Parseur from AI assistants (Claude, Cursor, …)

---

## ⚠️ Disclaimer about Localtunnel

When using the `parseur listen` command (with event listener support), your data is forwarded through **localtunnel servers**.

These servers are **not affiliated with Parseur** and are **not covered** by Parseur’s [Privacy Policy](https://parseur.com/privacy) or [Data Processing Agreement](https://parseur.com/dpa).

Data transmitted through localtunnel is **not encrypted end-to-end**.

➡️ **Use this feature at your own risk.**

For production-grade setups, we strongly recommend configuring your own secure webhook endpoint instead of relying on localtunnel.

---

## 🚀 Quick Start

### Install the package

```bash
pip install parseur-py
```

With event listener support (Flask + localtunnel)

```bash
pip install "parseur-py[listener]"
```

With MCP server support (use Parseur from AI assistants)

```bash
pip install "parseur-py[mcp]"
```

### Install the package from source

```bash
pip install -e .
```

### Build documentation

```bash
pip install -r requirements-doc.txt
cd docs
make html
```

### Run the tests

Unit tests run fully offline:

```bash
pytest
```

Integration tests hit the real Parseur API. They create and delete real
resources, so they're skipped unless credentials are provided **via the
environment** (never committed or stored in `~/.parseur.conf`):

```bash
PARSEUR_API_BASE=https://api.parseur.com \
PARSEUR_API_KEY=sk_your_key \
pytest tests/integration -v
```

---

### Initialize your configuration

Store your Parseur API credentials securely:

```bash
parseur init --api-key YOUR_PARSEUR_API_KEY
```

Your config is saved (by default) in:

```
~/.parseur.conf
```

---

### Example usage

List all your mailboxes:

```bash
parseur list-mailboxes
```

List documents in a mailbox:

```bash
parseur list-documents 12345
```

Upload a file to a mailbox (add `--wait` to block until it is parsed, with a live progress bar):

```bash
parseur upload-file 12345 ./path/to/document.pdf
parseur upload-file 12345 ./path/to/document.pdf --wait
```

Download a mailbox's results as a file (stdout by default, or `--output`):

```bash
parseur download-mailbox 12345 --format csv -o results.csv     # whole mailbox
parseur list-parser-fields 12345                               # find a table field id
parseur download-field 12345 PF951 --format xlsx -o lines.xlsx  # a table field
```

Register a custom webhook:

```bash
parseur create-webhook --event document.processed --target-url https://yourserver.com/webhook --mailbox-id 12345
```

Listen to events in real time (requires [listener]):

```bash
parseur listen --event document.processed --mailbox-id 12345
```

With forwarding:

```bash
parseur listen --event document.processed --mailbox-id 12345 --redirect-url http://localhost --redirect-port 8000
```

---

## 📜 CLI Commands

Run:

```bash
parseur --help
```

for a full list of available commands.

### Highlights

- **init**: Set your API token and (optional) base URL  
- **list-mailboxes**: Search and sort mailboxes  
- **get-mailbox**: Fetch a mailbox by ID  
- **get-mailbox-schema**: Get the mailbox parsing schema  
- **list-parser-fields**: List the fields extracted by a mailbox  
- **download-mailbox / download-field / download-export**: Download results as a file (csv/json/xlsx)  
- **list-export-configs**: List a mailbox's custom export configurations  
- **list-documents**: Advanced document search, filtering, sorting  
- **get-document / get-document-logs**: Fetch document details and processing logs  
- **reprocess-document / skip-document / copy-document / split-document / reverse-split-document / delete-document**: Document lifecycle operations  
- **upload-file / upload-text**: Upload new documents (add `--wait` for synchronous parsing)  
- **upload-folder**: Upload every file matching a glob path  
- **create-webhook / get-webhook / list-webhooks / delete-webhook**: Create, get, list, and delete custom webhook integrations.
- **enable-webhook / pause-webhook**: Activate or pause a webhook for a specific mailbox.
- **listen**: Create a temporary webhook and listen to events in real time (with optional redirect & silent mode)
- **mcp**: Run the Parseur MCP server so AI assistants can manage your account (requires `[mcp]`)

---

## 🔎 Advanced Search & Filtering

**Mailbox listing supports:**

- **Search** by name or email prefix
- **Sort** by:
  - name
  - document_count
  - template_count
  - PARSEDOK_count (processed)
  - PARSEDKO_count (failed)
  - QUOTAEXC_count (quota exceeded)
  - EXPORTKO_count (export failed)

**Document listing supports:**

- **Search** in:
  - document ID
  - document name
  - template name
  - email addresses (from, to, cc, bcc)
  - document metadata header
- **Sort** by:
  - name
  - created (received date)
  - processed date
  - status
- **Filter** by:
  - received_after / received_before dates
- **Include** parsed result in response

---

## ⚡ Webhooks Support

Easily register custom webhooks for events like:

- `document.processed`
- `document.processed.flattened`
- `document.template_needed`
- `document.export_failed`
- `table.processed`
- `table.processed.flattened`

Your webhook endpoint will receive POST notifications with Parseur payloads, enabling real-time integrations with your systems.

---

## 🤖 MCP Server (AI assistants)

**parseur-py** ships an [MCP](https://modelcontextprotocol.io) server that exposes Parseur as tools any MCP-compatible AI assistant (Claude Desktop, Codex, Cursor, Claude Code, and others) can call directly.

Start with [MCP.md](MCP.md) if you want to connect Parseur to Claude, Codex, or Cursor. It separates the recommended user setup from the developer setup and includes copy-paste configs for each client.

The full tool reference is in [MCP-TOOLS.md](MCP-TOOLS.md), and maintainer publishing instructions are in [MCP-PUBLISHING.md](MCP-PUBLISHING.md).

Quick zero-install command:

```bash
uvx --from "parseur-py[mcp]" parseur-py
```

---

## 🛠️ Configuration

Your API token and settings are stored in a simple INI file:

```
[parseur]
api_token = YOUR_API_KEY
base_url = https://api.parseur.com
```

You can customize the path by setting \`--config-path\` in your calls if needed.

---

## 🐍 Python Client Usage

Beyond the CLI, **parseur-py** is a standard Python library. Example:

```python
import parseur

parseur.api_key = "YOUR_API_KEY"

for mailbox in parseur.Mailbox.list():
    print(mailbox.name)
```

### Per-call API key override

Every method accepts an optional `api_key` argument that **takes priority over
the global `parseur.api_key`** for that single call — useful for multi-account
or multi-tenant code:

```python
parseur.Mailbox.list(api_key="sk_account_a")
parseur.Document.upload_file(123, "invoice.pdf", api_key="sk_account_b")
```

---

## 📖 Documentation

- [Parseur Official API Docs](https://help.parseur.com/en/articles/3566128-use-parseur-document-parsing-api)
- This package mirrors Parseur’s REST API, adding pagination handling, schema support, and convenient CLI commands.

---

## 💼 License

MIT License

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/foo`)
3. Commit your changes (`git commit -am 'Add foo'`)
4. Push to the branch (`git push origin feature/foo`)
5. Open a pull request

---

## ✨ Credits

Developed with ❤️ by the [Parseur](https://parseur.com) team.

---

*Parseur is the easiest way to automatically extract data from emails and documents. Stop copy-pasting data and automate your workflows!*
