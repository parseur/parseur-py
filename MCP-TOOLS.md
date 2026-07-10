# Parseur MCP Tools

The Parseur MCP server exposes the full client surface as **54 MCP tools**.

Each tool includes a title, description, argument descriptions, behavioral
annotations, and a structured JSON output schema. Destructive tools such as
`delete_*` are marked as destructive so MCP clients can ask for confirmation
before running them.

## Mailboxes

- `list_mailboxes`
- `get_mailbox`
- `get_mailbox_schema`
- `create_mailbox`
- `delete_mailbox`

## Mailbox Settings

These are separate tools instead of one generic update tool, so assistants can
choose the right action more reliably.

- `rename_mailbox`
- `set_ai_engine`
- `set_ai_instructions`
- `set_email_processing`
- `set_metadata`
- `set_timezone`
- `set_date_format`
- `set_decimal_separator`
- `set_allowed_extensions`
- `set_sender_filter`
- `split_by_ai`
- `split_by_page`
- `split_by_page_range`
- `split_by_keywords`
- `process_page_range`
- `process_odd_pages`
- `process_even_pages`

## Parser Fields

- `list_parser_fields`
- `add_parser_field`
- `update_parser_field`
- `delete_parser_field`

## Documents

- `list_documents`
- `get_document`
- `get_document_logs`
- `reprocess_document`
- `skip_document`
- `copy_document`
- `split_document`
- `reverse_split_document`
- `delete_document`

## Uploads

- `upload_file`
- `upload_text`
- `upload_file_and_wait`
- `upload_text_and_wait`
- `wait_for_document`

`upload_file` takes a file path and the server reads it directly. Give the
assistant an absolute path; no base64 encoding is needed.

## Webhooks

- `list_webhooks`
- `get_webhook`
- `create_webhook`
- `delete_webhook`
- `enable_webhook`
- `pause_webhook`

## Exports

- `get_mailbox_export`
- `get_table_export`
- `list_export_fields`
- `list_export_configs`
- `get_export_config`
- `create_export_config`
- `update_export_config`
- `delete_export_config`

Export tools return ready-to-use, self-authenticating `csv`, `json`, or `xlsx`
download links:

- `get_mailbox_export` exports the whole mailbox, one row per document.
- `get_table_export` exports a single table field, one row per line item.
- For a custom column selection, build an export config with `list_export_fields` and `create_export_config`.

## ID Conventions

- Mailboxes: integer id
- Webhooks: integer id
- Documents: string id
- Parser/table fields: `PF...` string id
- Export configs: integer id
