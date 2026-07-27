# Parseur MCP Server

Use Parseur directly from an MCP-compatible assistant such as Claude Desktop,
Claude Code, Codex, or Cursor.

The server runs locally on the client machine over stdio. It can therefore
upload local files and does not need an MCP host or port.

## Authentication

The local MCP server supports exactly two authentication methods. You only
need to configure one:

| Method | Recommended for | What you configure |
| --- | --- | --- |
| OAuth 2.0 | Desktop MCP clients and interactive use | No credential; only the stdio command |
| Parseur API key | Headless machines, CI, and automation | `PARSEUR_API_KEY` |

### Method 1: OAuth 2.0

If no API key is configured, `parseur-py` opens the Parseur login and consent
page when the MCP process starts. It uses Authorization Code with PKCE and
receives the result through a temporary callback on a free `127.0.0.1` port.
This callback is not the MCP server and is closed as soon as login finishes.
There is no `MCP_HOST` or `MCP_PORT` to configure.

OAuth credentials are stored in `~/.parseur.oauth.json` with user-only file
permissions. Access tokens are renewed automatically using the stored refresh
token. Do not put an OAuth access token in the MCP configuration.

You can sign in before starting the MCP client:

```bash
uvx --from "parseur-py[mcp]" parseur login
```

Use `parseur logout` to remove the locally stored OAuth credentials.

### Method 2: Parseur API key

Set `PARSEUR_API_KEY` in the environment of the MCP process:

```json
{
  "env": {
    "PARSEUR_API_KEY": "YOUR_PARSEUR_API_KEY"
  }
}
```

Alternatively, save the key once with:

```bash
parseur init --api-key YOUR_PARSEUR_API_KEY
```

The API key is then read from `~/.parseur.conf`. This method does not open a
browser.

### Which method is selected?

Authentication is selected in this order:

1. `PARSEUR_API_KEY`, when set by the MCP client.
2. The API key stored in `~/.parseur.conf`.
3. Stored OAuth credentials in `~/.parseur.oauth.json`.
4. If none exists, the OAuth login page opens automatically.

An API key therefore takes priority over OAuth. To switch from an API key to
OAuth, remove `PARSEUR_API_KEY` and the saved `api_key`, then run
`parseur login`.

## Claude

### Claude Desktop

Add a local stdio MCP server using:

```bash
uvx --from "parseur-py[mcp]" parseur-py
```

This configuration uses OAuth: because it contains no `PARSEUR_API_KEY`,
Parseur opens in your browser the first time Claude launches the server.

For API-key authentication, use this configuration:

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

### Claude Code

```bash
claude mcp add parseur -- uvx --from "parseur-py[mcp]" parseur-py
```

This command uses OAuth unless `PARSEUR_API_KEY` is supplied to the process.

## Codex

```bash
codex mcp add parseur -- uvx --from "parseur-py[mcp]" parseur-py
```

Or add the server to `~/.codex/config.toml`:

```toml
[mcp_servers.parseur]
command = "uvx"
args = ["--from", "parseur-py[mcp]", "parseur-py"]
```

## Cursor

Open **Settings → Tools & Integrations → MCP** and add:

```json
{
  "mcpServers": {
    "parseur": {
      "command": "uvx",
      "args": ["--from", "parseur-py[mcp]", "parseur-py"]
    }
  }
}
```

Cursor launches the local process, which opens the Parseur login flow. Add
`"env": {"PARSEUR_API_KEY": "YOUR_PARSEUR_API_KEY"}` to use an API key instead.

## Developer Installation

```bash
git clone https://github.com/parseur/parseur-py.git
cd parseur-py
pip install -e ".[mcp]"
```

Run the local stdio server:

```bash
parseur mcp
```

To test against a local Parseur API, point login and MCP at the same base:

```bash
PARSEUR_API_BASE=http://localhost:8000 parseur login --api-base http://localhost:8000
PARSEUR_API_BASE=http://localhost:8000 parseur mcp
```

## What To Try First

Ask your assistant:

```text
List my Parseur mailboxes.
```

Then try an end-to-end flow:

```text
Create a Parseur mailbox named "Vendor invoices", upload this PDF to it, wait
for parsing to finish, and show me the extracted result.
```

## How The Workflow Works

1. Create or choose a mailbox.
2. Upload a document with `upload_file` or `upload_text`.
3. Wait for parsing with `upload_file_and_wait`, `upload_text_and_wait`, or
   `wait_for_document`.
4. Read the parsed result.
5. Export data or push results to a webhook.

`upload_file` takes an absolute path. The server can read it because stdio runs
on the client machine. Destructive tools such as `delete_*` are marked as
destructive so MCP clients can ask for confirmation.

## Troubleshooting

### The server looks idle

Check that `uvx` works:

```bash
uvx --from "parseur-py[mcp]" parseur-py
```

An MCP stdio server waits silently for MCP messages. Stop it with `Ctrl+C`.

### Authentication fails

For OAuth, ensure no API key is configured, then run `parseur login` to restart
the browser flow. Do not paste an OAuth access token into the configuration.

For API-key authentication, verify `PARSEUR_API_KEY` and ensure the key is
still valid in Parseur.

### A file cannot be found

Use an absolute path:

```text
Upload /Users/alex/Documents/invoice.pdf to mailbox 12345.
```

## Reference

- Full tool list: [MCP-TOOLS.md](MCP-TOOLS.md)
- Registry publishing: [MCP-PUBLISHING.md](MCP-PUBLISHING.md)
- Server manifest: [server.json](server.json)
