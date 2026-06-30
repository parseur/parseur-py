import asyncio
from unittest.mock import MagicMock, patch

import pytest

# The MCP server is an optional feature; skip the whole module if the extra
# is not installed.
pytest.importorskip("mcp")

from parseur import mcp_server  # noqa: E402

EXPECTED_TOOLS = {
    "list_mailboxes",
    "get_mailbox",
    "get_mailbox_schema",
    "create_mailbox",
    "delete_mailbox",
    "rename_mailbox",
    "set_ai_engine",
    "set_ai_instructions",
    "set_email_processing",
    "set_metadata",
    "set_timezone",
    "set_date_format",
    "set_decimal_separator",
    "set_allowed_extensions",
    "set_sender_filter",
    "split_by_ai",
    "split_by_page",
    "split_by_page_range",
    "split_by_keywords",
    "process_page_range",
    "process_odd_pages",
    "process_even_pages",
    "list_parser_fields",
    "add_parser_field",
    "update_parser_field",
    "delete_parser_field",
    "list_documents",
    "get_document",
    "get_document_logs",
    "reprocess_document",
    "skip_document",
    "copy_document",
    "split_document",
    "reverse_split_document",
    "delete_document",
    "upload_file",
    "upload_text",
    "wait_for_document",
    "upload_file_and_wait",
    "upload_text_and_wait",
    "list_webhooks",
    "get_webhook",
    "create_webhook",
    "delete_webhook",
    "enable_webhook",
    "pause_webhook",
    "get_mailbox_export",
    "get_table_export",
    "list_export_fields",
    "list_export_configs",
    "get_export_config",
    "create_export_config",
    "update_export_config",
    "delete_export_config",
}


def test_all_tools_registered():
    tools = asyncio.run(mcp_server.mcp.list_tools())
    assert {t.name for t in tools} == EXPECTED_TOOLS


def test_tools_carry_full_metadata():
    tools = {t.name: t for t in asyncio.run(mcp_server.mcp.list_tools())}

    # Every tool has a title, a description, annotations, argument
    # descriptions, and a structured output schema.
    for tool in tools.values():
        assert tool.title, f"{tool.name} missing title"
        assert tool.description, f"{tool.name} missing description"
        assert tool.annotations is not None, f"{tool.name} missing annotations"
        assert tool.annotations.openWorldHint is True
        assert tool.outputSchema, f"{tool.name} missing output schema"
        for prop, schema in tool.inputSchema.get("properties", {}).items():
            assert schema.get("description"), f"{tool.name}.{prop} missing description"

    # Read-only vs destructive hints are set correctly.
    assert tools["list_mailboxes"].annotations.readOnlyHint is True
    assert tools["delete_document"].annotations.readOnlyHint is False
    assert tools["delete_document"].annotations.destructiveHint is True
    assert tools["delete_webhook"].annotations.destructiveHint is True


@patch("parseur.client.requests.get")
def test_list_mailboxes_tool(mock_get, mailbox_list_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mailbox_list_data
    mock_get.return_value = mock_response

    # call_tool exercises FastMCP's argument validation and result
    # serialization (including datetime fields on the mailbox).
    _, structured = asyncio.run(
        mcp_server.mcp.call_tool("list_mailboxes", {"search": "invoices"})
    )

    assert mock_get.called
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["search"] == "invoices"

    results = structured["result"]
    assert len(results) == len(mailbox_list_data["results"])
    assert results[0]["id"] == 153


@patch("parseur.client.requests.request")
def test_get_document_tool(mock_request, document_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = document_data
    mock_request.return_value = mock_response

    _, structured = asyncio.run(
        mcp_server.mcp.call_tool("get_document", {"document_id": "abc123"})
    )

    args, _ = mock_request.call_args
    assert args[0] == "GET"
    assert args[1].endswith("/document/abc123")
    assert structured["result"]["id"] == document_data["id"]


def test_ensure_api_key_reads_env(monkeypatch):
    monkeypatch.setenv("PARSEUR_API_KEY", "env-token")
    monkeypatch.setenv("PARSEUR_API_BASE", "https://example.test")
    mcp_server.ensure_api_key()

    import parseur

    assert parseur.api_key == "env-token"
    assert parseur.api_base == "https://example.test"
