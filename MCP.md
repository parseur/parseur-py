# Parseur MCP Server

Use Parseur directly from an MCP-compatible assistant such as Claude Desktop,
Claude Code, Codex, or Cursor.

With the Parseur MCP server, your assistant can list mailboxes, upload
documents, wait for parsing, read extracted results, create webhooks, and export
data without you writing API code.

## Start Here

Choose the path that matches what you are trying to do:

| You want to... | Use this path |
| --- | --- |
| Use Parseur from Claude, Codex, or Cursor | [User installation](#user-installation-recommended) |
| Work on `parseur-py` itself | [Developer installation](#developer-installation) |
| Publish the MCP server to the registry | [MCP-PUBLISHING.md](MCP-PUBLISHING.md) |
| See every available MCP tool | [MCP-TOOLS.md](MCP-TOOLS.md) |

## User Installation Recommended

This is the easiest setup for most users. You do not need to install
`parseur-py` globally. Your MCP client will start the server when it needs it.

You need:

- A Parseur API key
- [`uv`](https://docs.astral.sh/uv/) available on your machine
- One MCP client: Claude Desktop, Claude Code, Codex, or Cursor

The command your MCP client will run is:

```bash
uvx --from "parseur-py[mcp]" parseur-py
```

Why this is recommended:

- No virtualenv to manage
- No global Python package to update
- The assistant starts the server automatically
- Works well with Claude, Codex, and Cursor config files

If you prefer installing a local command yourself, use:

```bash
pip install "parseur-py[mcp]"
```

That exposes:

```bash
parseur-mcp
parseur mcp
```

## Developer Installation

Use this if you are changing `parseur-py` locally and want your assistant to run
your checkout instead of the PyPI release.

```bash
git clone https://github.com/parseur/parseur-py.git
cd parseur-py
pip install -e ".[mcp]"
```

Then configure your MCP client to run:

```bash
parseur-mcp
```

For direct debugging from the repository:

```bash
python -m parseur.mcp_server
```

## Authentication

The MCP server needs a Parseur API key.

Recommended: put the key in your MCP client config as `PARSEUR_API_KEY`. This is
the clearest setup because the assistant always starts the server with the right
credentials.

```json
"env": {
  "PARSEUR_API_KEY": "YOUR_PARSEUR_API_KEY"
}
```

Alternative: initialize the regular Parseur config once:

```bash
parseur init --api-key YOUR_PARSEUR_API_KEY
```

The MCP server reads credentials in this order:

1. `PARSEUR_API_KEY` environment variable
2. `~/.parseur.conf`

## Install In Claude

### Claude Code Command Line

For normal user installation:

```bash
claude mcp add parseur \
  -e PARSEUR_API_KEY=YOUR_PARSEUR_API_KEY \
  -- uvx --from "parseur-py[mcp]" parseur-py
```

For developer installation:

```bash
claude mcp add parseur \
  -e PARSEUR_API_KEY=YOUR_PARSEUR_API_KEY \
  -- parseur-mcp
```

Check that Claude sees it:

```bash
claude mcp list
```

### Claude Desktop Config

Add Parseur to `claude_desktop_config.json`.

Common locations:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

User installation:

```json
{
  "mcpServers": {
    "parseur": {
      "command": "uvx",
      "args": ["--from", "parseur-py[mcp]", "parseur-py"],
      "env": {
        "PARSEUR_API_KEY": "YOUR_PARSEUR_API_KEY"
      }
    }
  }
}
```

Developer installation:

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

Restart Claude Desktop after editing the file.

## Install In Codex

### Codex Command Line

For normal user installation:

```bash
codex mcp add parseur \
  --env PARSEUR_API_KEY=YOUR_PARSEUR_API_KEY \
  -- uvx --from "parseur-py[mcp]" parseur-py
```

For developer installation:

```bash
codex mcp add parseur \
  --env PARSEUR_API_KEY=YOUR_PARSEUR_API_KEY \
  -- parseur-mcp
```

Check that Codex sees it:

```bash
codex mcp list
```

### Codex Config File

You can also edit `~/.codex/config.toml`.

User installation:

```toml
[mcp_servers.parseur]
command = "uvx"
args = ["--from", "parseur-py[mcp]", "parseur-py"]
env = { PARSEUR_API_KEY = "YOUR_PARSEUR_API_KEY" }
```

Developer installation:

```toml
[mcp_servers.parseur]
command = "parseur-mcp"
env = { PARSEUR_API_KEY = "YOUR_PARSEUR_API_KEY" }
```

Restart Codex after editing the file.

## Install In Cursor

Cursor reads MCP servers from `.cursor/mcp.json` in a project, or from Cursor's
global MCP configuration.

### Cursor Project Config

Create `.cursor/mcp.json` in your project.

User installation:

```json
{
  "mcpServers": {
    "parseur": {
      "command": "uvx",
      "args": ["--from", "parseur-py[mcp]", "parseur-py"],
      "env": {
        "PARSEUR_API_KEY": "YOUR_PARSEUR_API_KEY"
      }
    }
  }
}
```

Developer installation:

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

Reload Cursor after editing the file.

### Cursor From The Command Line

For a new project-level config, you can create the file from the terminal.

User installation:

```bash
mkdir -p .cursor
cat > .cursor/mcp.json <<'JSON'
{
  "mcpServers": {
    "parseur": {
      "command": "uvx",
      "args": ["--from", "parseur-py[mcp]", "parseur-py"],
      "env": {
        "PARSEUR_API_KEY": "YOUR_PARSEUR_API_KEY"
      }
    }
  }
}
JSON
```

Developer installation:

```bash
mkdir -p .cursor
cat > .cursor/mcp.json <<'JSON'
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
JSON
```

If `.cursor/mcp.json` already contains other MCP servers, merge the `parseur`
block instead of replacing the whole file.

## What To Try First

Once Parseur is connected, ask your assistant something simple:

```text
List my Parseur mailboxes.
```

Then try an end-to-end flow:

```text
Create a Parseur mailbox named "Vendor invoices", upload this PDF to it, wait
for parsing to finish, and show me the extracted result.
```

For exports:

```text
Export the parsed results from mailbox 12345 as CSV.
```

## How The Workflow Works

The tools follow the normal Parseur mailbox lifecycle:

1. Create or choose a mailbox.
2. Upload a document with `upload_file` or `upload_text`.
3. Wait for parsing to finish with `upload_file_and_wait`, `upload_text_and_wait`, or `wait_for_document`.
4. Read the parsed result from the document.
5. Export data or push results to your own webhook.

Important details:

- `upload_file` takes an absolute file path. The MCP server runs locally, so it can read files from your machine.
- No base64 upload is needed.
- Parsing is asynchronous. Use the `*_and_wait` tools when you want the assistant to wait for the final result.
- Destructive tools such as `delete_*` are marked as destructive so clients can ask for confirmation.

## Troubleshooting

### The assistant says the server is unavailable

Check that `uvx` works:

```bash
uvx --from "parseur-py[mcp]" parseur-py
```

The command starts an MCP stdio server and waits for MCP messages, so it may look
idle. Stop it with `Ctrl+C`.

### Authentication fails

Make sure the config contains:

```json
"env": {
  "PARSEUR_API_KEY": "YOUR_PARSEUR_API_KEY"
}
```

Also check that the key is valid in Parseur.

### The assistant cannot find a file to upload

Use an absolute path:

```text
Upload /Users/alex/Documents/invoice.pdf to mailbox 12345.
```

### I already have other MCP servers configured

Do not replace the whole config file. Add only the `parseur` entry inside the
existing `mcpServers` object.

## Reference

- Full tool list: [MCP-TOOLS.md](MCP-TOOLS.md)
- Registry publishing: [MCP-PUBLISHING.md](MCP-PUBLISHING.md)
- Server manifest: [server.json](server.json)
