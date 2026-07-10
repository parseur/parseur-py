# Publishing the Parseur MCP Server

This document is for maintainers publishing the Parseur MCP server to the
official [MCP Registry](https://registry.modelcontextprotocol.io).

The server is described by [`server.json`](server.json) and is published
under the `io.github.parseur/parseur-py` name. Ownership is verified through the
GitHub `parseur` organization and the `<!-- mcp-name:
io.github.parseur/parseur-py -->` marker shipped in the README, so it is
present in the PyPI package.

## Before You Publish

Check these first:

- `server.json` top-level `version` matches the release.
- `server.json` `packages[].version` matches the same release.
- The matching `parseur-py` version is already published on PyPI.
- The PyPI README contains the `<!-- mcp-name: io.github.parseur/parseur-py -->` marker.
- You are authenticated with a GitHub account that belongs to the `parseur` organization.

## Publish manually

```bash
# 1. Install the publisher CLI
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher

# 2. Authenticate (opens GitHub; you must be a member of the `parseur` org)
./mcp-publisher login github

# 3. Publish the version described in server.json
./mcp-publisher publish
```

## Automated publishing

A GitHub Actions workflow (`.github/workflows/publish-mcp-registry.yml`) does
this automatically on each GitHub release using GitHub OIDC. Prefer the
automated workflow for normal releases; use manual publishing only for recovery
or registry-specific maintenance.

## Client command after publishing

Once published, clients install and run the server with:

```bash
uvx --from "parseur-py[mcp]" parseur-py
```
