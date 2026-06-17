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
pip install parseur-py[listener]
```

With MCP server support (use Parseur from AI assistants)

```bash
pip install parseur-py[mcp]
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

**parseur-py** ships an [MCP](https://modelcontextprotocol.io) server that exposes Parseur as tools any MCP-compatible AI assistant (Claude Desktop, Cursor, Claude Code, …) can call directly — listing mailboxes, uploading documents, reading parsed results, managing webhooks, and more.

### Install

```bash
pip install parseur-py[mcp]
```

### Run

The server speaks MCP over **stdio**. It reads your API key from `~/.parseur.conf` (run `parseur init` first) or from the `PARSEUR_API_KEY` environment variable.

```bash
parseur mcp
```

You can also launch it via the dedicated console script or as a module:

```bash
parseur-mcp
python -m parseur.mcp_server
```

### Configure your client

Add Parseur to your MCP client config. Example for **Claude Desktop**
(`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "parseur": {
      "command": "parseur-mcp",
      "env": {
        "PARSEUR_API_KEY": "YOUR_PARSEUR_API_KEY"
      }
    }
  }
}
```

### Available tools

Every tool carries a title, a description, per-argument descriptions, behavioral
annotations (read-only / destructive / idempotent / open-world hints), and a
structured JSON output schema — so the assistant understands exactly what each
command does, what it expects, and what it returns. Destructive tools
(`delete_*`) are flagged so clients can ask for confirmation first.

The server exposes the full client surface as **54 MCP tools**:

- **Mailboxes**: `list_mailboxes`, `get_mailbox`, `get_mailbox_schema`, `create_mailbox`, `delete_mailbox`
- **Mailbox settings** (one tool per setting, instead of a generic update): `rename_mailbox`, `set_ai_engine`, `set_ai_instructions`, `set_email_processing`, `set_metadata`, `set_timezone`, `set_date_format`, `set_decimal_separator`, `set_allowed_extensions`, `set_sender_filter`, `split_by_ai`, `split_by_page`, `split_by_page_range`, `split_by_keywords`, `process_page_range`, `process_odd_pages`, `process_even_pages`
- **Parser fields**: `list_parser_fields`, `add_parser_field`, `update_parser_field`, `delete_parser_field`
- **Documents**: `list_documents`, `get_document`, `get_document_logs`, `reprocess_document`, `skip_document`, `copy_document`, `split_document`, `reverse_split_document`, `delete_document`
- **Uploads**: `upload_file`, `upload_text` (asynchronous) and `upload_file_and_wait`, `upload_text_and_wait`, `wait_for_document` (block until parsed)
- **Webhooks**: `list_webhooks`, `get_webhook`, `create_webhook`, `delete_webhook`, `enable_webhook`, `pause_webhook`
- **Exports**: `get_mailbox_export`, `get_table_export`, `list_export_fields`, `list_export_configs`, `get_export_config`, `create_export_config`, `update_export_config`, `delete_export_config`

> **Uploading files over MCP:** `upload_file` takes a **file path** and the server reads it directly — just give the absolute path, no base64. When the desktop app launches the server locally (the usual setup) it runs on your machine, so it can read your files; no extra permission/config is needed (this server is not sandboxed to specific folders). To copy a document that is already in another mailbox, use `copy_document` instead — no file transfer at all.

> **Getting results out as a file:** three kinds of export, each returning ready-to-use, self-authenticating `csv` / `json` / `xlsx` download links you can hand to the user. `get_mailbox_export` exports the whole mailbox (one row per document); `get_table_export` exports a single table field's rows (one row per line item); for a custom column selection, build an export config with `list_export_fields` + `create_export_config`.

### Workflow

The tools follow the lifecycle of a mailbox — the server ships these same instructions so the assistant can follow the flow on its own:

1. **Create a mailbox** with just a title (`create_mailbox`). Don't define fields up front: Parseur auto-detects them from the first documents during its identification phase. Adjust them afterwards with `add_parser_field` / `update_parser_field` / `delete_parser_field`.
2. **Send documents** to parse with `upload_file` (a path on the server's machine) or `upload_text` (email/HTML content).
3. **Wait for the result.** Parsing is asynchronous: a document is pending while its status is `INCOMING` / `ANALYZING` / `PROGRESS` and finished at `PARSEDOK` (or `PARSEDKO` / `EXPORTKO`). The parsed data is in the document's `result` field, populated only once it reaches `PARSEDOK`. Prefer `upload_file_and_wait` / `upload_text_and_wait` to get it in one call, or `wait_for_document` to wait on an existing document.
4. **Get the data out** as a file via the three exports above, or push each parsed document to a URL in real time with `create_webhook`.

IDs follow a simple convention: mailboxes and webhooks use an integer id, documents a string id, parser/table fields a `PF...` string id, and export configs an integer id.

### Publishing to the MCP Registry

The server is described by [`server.json`](server.json) and can be published to the official [MCP Registry](https://registry.modelcontextprotocol.io) under the `io.github.parseur/parseur-py` name. Ownership is verified through the GitHub `parseur` organization and the `<!-- mcp-name: io.github.parseur/parseur-py -->` marker shipped in this README (so it is present in the PyPI package).

```bash
# 1. Install the publisher CLI
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher

# 2. Authenticate (opens GitHub; you must be a member of the `parseur` org)
./mcp-publisher login github

# 3. Publish the version described in server.json
./mcp-publisher publish
```

Before publishing, make sure the version in `server.json` (both the top-level `version` and `packages[].version`) matches a release of `parseur-py` already on PyPI whose README contains the `mcp-name` marker. A GitHub Actions workflow (`.github/workflows/publish-mcp-registry.yml`) does this automatically on each GitHub release using GitHub OIDC.

Once published, clients install and run the server with:

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
