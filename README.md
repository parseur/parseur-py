# 🤖🧙parseur-py

**parseur-py** is a modern Python client for the [Parseur](https://parseur.com) API.

It lets you **manage mailboxes, documents, uploads, and webhooks** programmatically or from the command line.

Built to help you automate document parsing at scale, parseur-py makes integrating with Parseur fast, easy, and Pythonic.

[![GitHub Repo](https://img.shields.io/badge/GitHub-parseur--py-blue?logo=github)](https://github.com/parseur/parseur-py)
[![PyPI version](https://badge.fury.io/py/parseur-py.svg)](https://badge.fury.io/py/parseur-py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Read the Docs](https://readthedocs.org/projects/parseur-py/badge/?version=latest)](https://parseur-py.readthedocs.io/en/latest/?badge=latest)

---

## ✨ Features

✅ List, search, and sort mailboxes  
✅ Get mailbox details and schema  
✅ List, search, filter, and sort documents  
✅ Upload documents by file or email content  
✅ Reprocess, skip, copy, or delete documents  
✅ Manage custom webhooks for real-time events  
✅ Fully-featured **Command Line Interface (CLI)**

---

## 🚀 Quick Start

### Install the package

```bash
pip install parseur-py
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

Upload a file to a mailbox:

```bash
parseur upload-file 12345 ./path/to/document.pdf
```

Register a custom webhook:

```bash
parseur create-webhook --event document.processed --target-url https://yourserver.com/webhook --mailbox-id 12345
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
- **list-documents**: Advanced document search, filtering, sorting  
- **get-document**: Fetch document details  
- **reprocess-document / skip-document / delete-document**: Document lifecycle operations  
- **upload-file / upload-text**: Upload new documents  
- **create-webhook / get-webhook / list-webhooks / delete-webhook**: Create, get, list, and delete custom webhook integrations.
- **enable-webhook / pause-webhook**: Activate or pause a webhook for a specific mailbox.

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
