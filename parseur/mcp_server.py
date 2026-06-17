"""Model Context Protocol (MCP) server for Parseur.

Exposes the parseur-py library as MCP tools so AI assistants (Claude Desktop,
Cursor, etc.) can manage Parseur mailboxes, parser fields, documents, exports,
and webhooks.

Every tool carries a human-readable title, a description, per-argument
descriptions, behavioral annotations (read-only / destructive / idempotent /
open-world hints), and structured JSON output so the assistant can reason
about what each command does and what it returns.

Requires the ``mcp`` extra::

    pip install parseur-py[mcp]

Run it with::

    parseur mcp

or directly::

    python -m parseur.mcp_server
"""

import os
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations
except ImportError as e:  # pragma: no cover - exercised only without the extra
    raise ImportError(
        "The MCP server requires the 'mcp' package. "
        "Please install with: pip install parseur-py[mcp]"
    ) from e

from pydantic import Field

import parseur
from parseur import (
    DateFormat,
    DecimalSeparator,
    Document,
    DocumentOrderKey,
    DocumentStatus,
    EmailProcessing,
    ExportConfig,
    FAILED_STATUSES,
    FINAL_STATUSES,
    Mailbox,
    MailboxOrderKey,
    Metadata,
    PENDING_STATUSES,
    ParseurEvent,
    ParserField,
    SenderFilter,
    Webhook,
)


class ParseurMCP(FastMCP):
    """FastMCP that fills in its instructions lazily, once all tools exist.

    ``instructions`` is a construction-time argument in FastMCP, but ours is an
    f-string referencing each tool's ``__name__`` — it can only be built after
    the tool functions are defined, and those need ``mcp`` to exist first. So
    instead of passing the text up front, we inject it when the initialization
    options are built (the single point every transport goes through, just
    before the handshake), by which time ``INSTRUCTIONS`` is defined.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        build_options = self._mcp_server.create_initialization_options

        def create_initialization_options(*a: Any, **k: Any):
            return build_options(*a, **k).model_copy(
                update={"instructions": INSTRUCTIONS}
            )

        self._mcp_server.create_initialization_options = create_initialization_options


mcp = ParseurMCP("parseur")


def ensure_api_key():
    """Allow overriding the configured API key/base via environment variables.

    MCP clients usually inject credentials through the server's environment,
    so ``PARSEUR_API_KEY`` (and optionally ``PARSEUR_API_BASE``) take
    precedence over the values loaded from ``~/.parseur.conf``.
    """
    env_key = os.environ.get("PARSEUR_API_KEY")
    env_base = os.environ.get("PARSEUR_API_BASE")
    if env_key:
        parseur.api_key = env_key
    if env_base:
        parseur.api_base = env_base


# Annotation presets. ``openWorldHint`` is True for every tool because they all
# talk to the remote Parseur API.
READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
WRITE = ToolAnnotations(readOnlyHint=False, openWorldHint=True)
WRITE_IDEMPOTENT = ToolAnnotations(
    readOnlyHint=False, idempotentHint=True, openWorldHint=True
)
DESTRUCTIVE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=True
)


# Reusable annotated argument types.
MailboxId = Annotated[int, Field(description="The integer id of the mailbox (parser).")]
DocumentId = Annotated[str, Field(description="The string id of the document.")]
WebhookId = Annotated[int, Field(description="The integer id of the webhook.")]


# Document statuses rendered for tool descriptions and the instructions, in
# enum-declaration order (a frozenset has no order) and wrapped in backticks.
PENDING_STATUS_LIST = " / ".join(
    f"`{status.value}`" for status in DocumentStatus if status.value in PENDING_STATUSES
)
FINAL_STATUS_LIST = ", ".join(
    f"`{status.value}`" for status in DocumentStatus if status.value in FINAL_STATUSES
)
FAILED_STATUS_LIST = ", ".join(
    f"`{status.value}`" for status in DocumentStatus if status.value in FAILED_STATUSES
)


# ------------------------
# Mailbox tools
# ------------------------


@mcp.tool(
    title="List mailboxes",
    description=(
        "List all mailboxes (parsers) on the account, with optional search and "
        "sorting. Returns the full list, handling pagination automatically."
    ),
    annotations=READ_ONLY,
    structured_output=True,
)
def list_mailboxes(
    search: Annotated[
        Optional[str],
        Field(description="Filter by mailbox name or email prefix."),
    ] = None,
    order_by: Annotated[
        Optional[str],
        Field(
            description=(
                "Sort field. One of: name, document_count, template_count, "
                "PARSEDOK_count, PARSEDKO_count, QUOTAEXC_count, EXPORTKO_count."
            )
        ),
    ] = None,
    descending: Annotated[
        bool,
        Field(description="Sort in descending order (default is ascending)."),
    ] = False,
) -> List[Dict[str, Any]]:
    order_by_enum = MailboxOrderKey(order_by) if order_by else None
    return Mailbox.list(
        search=search,
        order_by=order_by_enum,
        ascending=not descending,
    )


@mcp.tool(
    title="Get mailbox",
    description="Get the full details of a single mailbox by its id.",
    annotations=READ_ONLY,
    structured_output=True,
)
def get_mailbox(mailbox_id: MailboxId) -> Dict[str, Any]:
    return Mailbox.retrieve(mailbox_id)


@mcp.tool(
    title="Get mailbox schema",
    description=(
        "Get the parsing schema of a mailbox: the list of fields extracted from "
        "documents, with their names and types."
    ),
    annotations=READ_ONLY,
    structured_output=True,
)
def get_mailbox_schema(mailbox_id: MailboxId) -> Dict[str, Any]:
    return Mailbox.schema(mailbox_id)


AI_ENGINE_DESC = (
    "AI engine for the mailbox. One of: "
    + ", ".join(e.value for e in parseur.AIEngine)
    + ". Defaults to GCP_AI_2 (AI Vision engine) when omitted."
)


@mcp.tool(
    title="Create mailbox",
    description=(
        "Create a new mailbox (parser). Normally you only pass a title (name) — "
        "do NOT define fields here. Parseur auto-detects the fields from the "
        "first documents during its identification phase. Once identification "
        "is done you can adjust the fields with add_parser_field / "
        "update_parser_field. The AI Vision engine is used by default; "
        "ai_engine and ai_instructions are advanced, optional overrides."
    ),
    annotations=WRITE,
    structured_output=True,
)
def create_mailbox(
    name: Annotated[
        Optional[str],
        Field(description="Title of the mailbox. Parseur generates one if omitted."),
    ] = None,
    ai_engine: Annotated[Optional[str], Field(description=AI_ENGINE_DESC)] = None,
    ai_instructions: Annotated[
        Optional[str],
        Field(description="Optional natural-language extraction instructions."),
    ] = None,
) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    if ai_instructions is not None:
        fields["ai_instructions"] = ai_instructions
    return Mailbox.create(name=name, ai_engine=ai_engine, **fields)


@mcp.tool(
    title="Rename mailbox",
    description="Rename a mailbox.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def rename_mailbox(
    mailbox_id: MailboxId,
    name: Annotated[str, Field(description="New display name for the mailbox.")],
) -> Dict[str, Any]:
    return Mailbox.rename(mailbox_id, name)


@mcp.tool(
    title="Set AI engine",
    description="Set the AI engine a mailbox uses to extract data.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def set_ai_engine(
    mailbox_id: MailboxId,
    ai_engine: Annotated[str, Field(description=AI_ENGINE_DESC)],
) -> Dict[str, Any]:
    return Mailbox.set_ai_engine(mailbox_id, ai_engine)


@mcp.tool(
    title="Set AI instructions",
    description=(
        "Set the natural-language extraction instructions for a mailbox, or clear "
        "them (pass null)."
    ),
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def set_ai_instructions(
    mailbox_id: MailboxId,
    instructions: Annotated[
        Optional[str],
        Field(description="Extraction instructions, or null to clear them."),
    ] = None,
) -> Dict[str, Any]:
    return Mailbox.set_ai_instructions(mailbox_id, instructions)


# Each mailbox setting is exposed through its dedicated Mailbox helper (rather
# than a single generic update), so every option is discoverable and validated.

EMAIL_PROCESSING_DESC = (
    "How incoming emails are processed. One of: "
    + ", ".join(e.value for e in EmailProcessing)
    + "."
)
DATE_FORMAT_DESC = (
    "How ambiguous dates in documents are read. One of: "
    + ", ".join(e.value for e in DateFormat)
    + "; or null to auto-detect."
)
DECIMAL_SEPARATOR_DESC = (
    "Decimal separator for numbers in documents. One of: "
    + ", ".join(repr(e.value) for e in DecimalSeparator)
    + "; or null to clear."
)
SENDER_FILTER_DESC = (
    "Sender filter mode. One of: " + ", ".join(e.value for e in SenderFilter) + "."
)
METADATA_COLUMNS_DESC = "Each one of: " + ", ".join(m.name for m in Metadata) + "."
PAGE_RANGES_DESC = (
    'Page ranges, e.g. [{"start_index": 1, "end_index": 5}, '
    '{"start_index": 6, "end_index": null}] (null end means "to the last page").'
)


@mcp.tool(
    title="Set email processing",
    description="Choose how a mailbox processes incoming emails and their attachments.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def set_email_processing(
    mailbox_id: MailboxId,
    mode: Annotated[str, Field(description=EMAIL_PROCESSING_DESC)],
) -> Dict[str, Any]:
    return Mailbox.set_email_processing(mailbox_id, mode)


@mcp.tool(
    title="Set metadata columns",
    description=(
        "Enable and/or disable per-document metadata columns on a mailbox, in one "
        "call. Columns not listed are left unchanged."
    ),
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def set_metadata(
    mailbox_id: MailboxId,
    enable: Annotated[
        List[str], Field(description="Columns to enable. " + METADATA_COLUMNS_DESC)
    ] = [],
    disable: Annotated[
        List[str], Field(description="Columns to disable. " + METADATA_COLUMNS_DESC)
    ] = [],
) -> Dict[str, Any]:
    enable_flag = Metadata(0)
    for name in enable:
        enable_flag |= Metadata[name]
    disable_flag = Metadata(0)
    for name in disable:
        disable_flag |= Metadata[name]
    return Mailbox.set_metadata(mailbox_id, enable=enable_flag, disable=disable_flag)


@mcp.tool(
    title="Set timezone",
    description="Set the timezone used to interpret dates/times in a mailbox's documents.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def set_timezone(
    mailbox_id: MailboxId,
    timezone: Annotated[
        Optional[str],
        Field(description="IANA timezone (e.g. 'Europe/Paris'), or null to clear."),
    ] = None,
) -> Dict[str, Any]:
    return Mailbox.set_timezone(mailbox_id, timezone)


@mcp.tool(
    title="Set date format",
    description="Set how ambiguous dates in a mailbox's documents are read.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def set_date_format(
    mailbox_id: MailboxId,
    date_format: Annotated[Optional[str], Field(description=DATE_FORMAT_DESC)] = None,
) -> Dict[str, Any]:
    return Mailbox.set_date_format(mailbox_id, date_format)


@mcp.tool(
    title="Set decimal separator",
    description="Set the decimal separator for numbers in a mailbox's documents.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def set_decimal_separator(
    mailbox_id: MailboxId,
    separator: Annotated[
        Optional[str], Field(description=DECIMAL_SEPARATOR_DESC)
    ] = None,
) -> Dict[str, Any]:
    return Mailbox.set_decimal_separator(mailbox_id, separator)


@mcp.tool(
    title="Set allowed file types",
    description=(
        "Restrict which file types ('Files to process') a mailbox accepts. Pass "
        "null/empty to accept every supported type."
    ),
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def set_allowed_extensions(
    mailbox_id: MailboxId,
    extensions: Annotated[
        Optional[List[str]],
        Field(
            description=(
                "Extensions to accept, e.g. ['pdf', 'docx', 'png']. Supported: "
                + ", ".join(sorted(parseur.SUPPORTED_FILE_EXTENSIONS))
                + "."
            )
        ),
    ] = None,
) -> Dict[str, Any]:
    return Mailbox.set_allowed_extensions(mailbox_id, extensions)


@mcp.tool(
    title="Set sender filter",
    description=(
        "Filter which senders a mailbox accepts, by an allow- or block-list. Pass "
        "an empty list to clear the filter."
    ),
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def set_sender_filter(
    mailbox_id: MailboxId,
    mode: Annotated[str, Field(description=SENDER_FILTER_DESC)],
    emails_or_domains: Annotated[
        List[str],
        Field(description="Emails or domains to allow/block, e.g. ['acme.com']."),
    ],
) -> Dict[str, Any]:
    return Mailbox.set_sender_filter(mailbox_id, mode, emails_or_domains)


@mcp.tool(
    title="Configure AI splitting",
    description=(
        "Enable or disable splitting a mailbox's documents with AI. The split runs "
        "per document via split_document."
    ),
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def split_by_ai(
    mailbox_id: MailboxId,
    instructions: Annotated[
        Optional[str], Field(description="Optional AI splitting instructions.")
    ] = None,
    enabled: Annotated[
        bool, Field(description="Set to false to turn AI splitting off.")
    ] = True,
) -> Dict[str, Any]:
    return Mailbox.split_by_ai(mailbox_id, instructions, enabled=enabled)


@mcp.tool(
    title="Configure splitting every N pages",
    description="Enable or disable splitting a mailbox's documents every N pages.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def split_by_page(
    mailbox_id: MailboxId,
    every: Annotated[
        Optional[int],
        Field(description="Pages per resulting document (required unless disabling)."),
    ] = None,
    enabled: Annotated[
        bool, Field(description="Set to false to turn this split method off.")
    ] = True,
) -> Dict[str, Any]:
    return Mailbox.split_by_page(mailbox_id, every, enabled=enabled)


@mcp.tool(
    title="Configure splitting by page range",
    description="Enable or disable splitting a mailbox's documents by explicit page ranges.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def split_by_page_range(
    mailbox_id: MailboxId,
    ranges: Annotated[
        Optional[List[Dict[str, Any]]],
        Field(description=PAGE_RANGES_DESC + " Required unless disabling."),
    ] = None,
    enabled: Annotated[
        bool, Field(description="Set to false to clear this split method.")
    ] = True,
) -> Dict[str, Any]:
    return Mailbox.split_by_page_range(mailbox_id, ranges, enabled=enabled)


@mcp.tool(
    title="Configure splitting by keywords",
    description="Enable or disable splitting a mailbox's documents on keywords.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def split_by_keywords(
    mailbox_id: MailboxId,
    keywords: Annotated[
        Optional[List[Dict[str, Any]]],
        Field(
            description=(
                'Keywords, e.g. [{"keyword": "Invoice", "is_before": true}] '
                "(is_before splits before vs after the keyword). Required unless "
                "disabling."
            )
        ),
    ] = None,
    enabled: Annotated[
        bool, Field(description="Set to false to clear this split method.")
    ] = True,
) -> Dict[str, Any]:
    return Mailbox.split_by_keywords(mailbox_id, keywords, enabled=enabled)


@mcp.tool(
    title="Restrict processing to page ranges",
    description=(
        "Restrict a mailbox to process only the given page ranges of each document "
        "(or clear the restriction)."
    ),
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def process_page_range(
    mailbox_id: MailboxId,
    ranges: Annotated[
        Optional[List[Dict[str, Any]]],
        Field(description=PAGE_RANGES_DESC + " Required unless disabling."),
    ] = None,
    enabled: Annotated[
        bool, Field(description="Set to false to process every page again.")
    ] = True,
) -> Dict[str, Any]:
    return Mailbox.process_page_range(mailbox_id, ranges, enabled=enabled)


@mcp.tool(
    title="Process odd pages only",
    description="Restrict a mailbox to process only odd pages (1, 3, 5, ...) of each document.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def process_odd_pages(
    mailbox_id: MailboxId,
    enabled: Annotated[
        bool, Field(description="Set to false to process all pages again.")
    ] = True,
) -> Dict[str, Any]:
    return Mailbox.process_odd_pages(mailbox_id, enabled=enabled)


@mcp.tool(
    title="Process even pages only",
    description="Restrict a mailbox to process only even pages (2, 4, 6, ...) of each document.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def process_even_pages(
    mailbox_id: MailboxId,
    enabled: Annotated[
        bool, Field(description="Set to false to process all pages again.")
    ] = True,
) -> Dict[str, Any]:
    return Mailbox.process_even_pages(mailbox_id, enabled=enabled)


@mcp.tool(
    title="Delete mailbox",
    description=(
        "Permanently delete a mailbox and all of its documents. This cannot be "
        "undone; confirm with the user first."
    ),
    annotations=DESTRUCTIVE,
    structured_output=True,
)
def delete_mailbox(mailbox_id: MailboxId) -> Dict[str, Any]:
    Mailbox.delete(mailbox_id)
    return {"deleted": True, "mailbox_id": mailbox_id}


# ------------------------
# Parser field tools
# ------------------------

FIELD_FORMAT_DESC = "Field format. One of: " + ", ".join(
    e.value for e in parseur.FieldFormat
)
FieldId = Annotated[
    str, Field(description='The string id of the parser field (e.g. "PF12345").')
]


@mcp.tool(
    title="List parser fields",
    description="List the fields (parser_object_set) extracted by a mailbox.",
    annotations=READ_ONLY,
    structured_output=True,
)
def list_parser_fields(mailbox_id: MailboxId) -> List[Dict[str, Any]]:
    return ParserField.list(mailbox_id)


@mcp.tool(
    title="Add parser field",
    description=(
        "Add a new field to a mailbox, keeping its existing fields. Returns the "
        "updated list of fields."
    ),
    annotations=WRITE,
    structured_output=True,
)
def add_parser_field(
    mailbox_id: MailboxId,
    name: Annotated[str, Field(description="Name of the new field.")],
    field_format: Annotated[str, Field(description=FIELD_FORMAT_DESC)],
    query: Annotated[
        Optional[str],
        Field(description="Optional AI extraction instructions for the field."),
    ] = None,
    is_required: Annotated[
        Optional[bool], Field(description="Whether the field is required.")
    ] = None,
    choice_set: Annotated[
        Optional[List[str]],
        Field(description="Optional list of allowed values for the field."),
    ] = None,
) -> List[Dict[str, Any]]:
    return ParserField.add(
        mailbox_id,
        name,
        field_format,
        query=query,
        is_required=is_required,
        choice_set=choice_set,
    )


@mcp.tool(
    title="Update parser field",
    description=(
        "Update a single existing field of a mailbox by its id. Only the "
        "provided properties change; the others are preserved. Returns the "
        "updated list of fields."
    ),
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def update_parser_field(
    mailbox_id: MailboxId,
    field_id: FieldId,
    name: Annotated[Optional[str], Field(description="New name for the field.")] = None,
    field_format: Annotated[Optional[str], Field(description=FIELD_FORMAT_DESC)] = None,
    query: Annotated[
        Optional[str], Field(description="New AI extraction instructions.")
    ] = None,
    is_required: Annotated[
        Optional[bool], Field(description="Whether the field is required.")
    ] = None,
    choice_set: Annotated[
        Optional[List[str]],
        Field(description="New list of allowed values for the field."),
    ] = None,
) -> List[Dict[str, Any]]:
    changes: Dict[str, Any] = {}
    if name is not None:
        changes["name"] = name
    if field_format is not None:
        changes["field_format"] = field_format
    if query is not None:
        changes["query"] = query
    if is_required is not None:
        changes["is_required"] = is_required
    if choice_set is not None:
        changes["choice_set"] = choice_set
    return ParserField.update(mailbox_id, field_id, **changes)


@mcp.tool(
    title="Delete parser field",
    description=(
        "Delete a field from a mailbox by its id. Returns the updated list of "
        "fields. Confirm with the user first."
    ),
    annotations=DESTRUCTIVE,
    structured_output=True,
)
def delete_parser_field(
    mailbox_id: MailboxId, field_id: FieldId
) -> List[Dict[str, Any]]:
    return ParserField.delete(mailbox_id, field_id)


# ------------------------
# Document tools
# ------------------------


@mcp.tool(
    title="List documents",
    description=(
        "List documents in a mailbox, with optional search, sorting, date "
        "filtering, and parsed-result inclusion. Handles pagination."
    ),
    annotations=READ_ONLY,
    structured_output=True,
)
def list_documents(
    mailbox_id: MailboxId,
    search: Annotated[
        Optional[str],
        Field(
            description=(
                "Match document id, name, template name, from/to/cc/bcc email "
                "addresses, or document metadata."
            )
        ),
    ] = None,
    order_by: Annotated[
        Optional[str],
        Field(description="Sort field. One of: name, created, processed, status."),
    ] = None,
    descending: Annotated[
        bool,
        Field(description="Sort in descending order (default is ascending)."),
    ] = False,
    received_after: Annotated[
        Optional[str],
        Field(description="Only documents received on/after this date (YYYY-MM-DD)."),
    ] = None,
    received_before: Annotated[
        Optional[str],
        Field(description="Only documents received on/before this date (YYYY-MM-DD)."),
    ] = None,
    with_result: Annotated[
        bool,
        Field(description="Include the parsed result of each document."),
    ] = False,
) -> List[Dict[str, Any]]:
    order_by_enum = DocumentOrderKey(order_by) if order_by else None
    after = datetime.strptime(received_after, "%Y-%m-%d") if received_after else None
    before = datetime.strptime(received_before, "%Y-%m-%d") if received_before else None
    return Document.list(
        mailbox_id,
        search=search,
        order_by=order_by_enum,
        ascending=not descending,
        received_after=after,
        received_before=before,
        with_result=with_result,
    )


@mcp.tool(
    title="Get document",
    description=(
        f"Get the details of a single document. The extracted data is in its "
        f"`result` field, populated once the document's status is "
        f"`{DocumentStatus.PARSEDOK.value}` (empty while still "
        f"{PENDING_STATUS_LIST})."
    ),
    annotations=READ_ONLY,
    structured_output=True,
)
def get_document(document_id: DocumentId) -> Dict[str, Any]:
    return Document.retrieve(document_id)


@mcp.tool(
    title="Get document logs",
    description="Get the processing/activity logs of a document.",
    annotations=READ_ONLY,
    structured_output=True,
)
def get_document_logs(document_id: DocumentId) -> List[Dict[str, Any]]:
    return Document.logs(document_id)


@mcp.tool(
    title="Reprocess document",
    description=(
        "Re-run parsing on a document. Asynchronous: returns a notification_set "
        "(messages keyed by info / success / warning / error), not the document. "
        "Use get_document or wait_for_document to observe the new result."
    ),
    annotations=WRITE,
    structured_output=True,
)
def reprocess_document(document_id: DocumentId) -> Dict[str, Any]:
    return Document.reprocess(document_id)


@mcp.tool(
    title="Skip document",
    description="Mark a document as skipped and return the updated document.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def skip_document(document_id: DocumentId) -> Dict[str, Any]:
    return Document.skip(document_id)


@mcp.tool(
    title="Copy document",
    description=(
        "Copy a document into another mailbox. Creates a new document each time "
        "it is called. Asynchronous: returns a notification_set (messages keyed "
        "by info / success / warning / error), not the new document."
    ),
    annotations=WRITE,
    structured_output=True,
)
def copy_document(
    document_id: DocumentId,
    target_mailbox_id: Annotated[
        int, Field(description="The mailbox id to copy the document into.")
    ],
) -> Dict[str, Any]:
    return Document.copy(document_id, target_mailbox_id)


@mcp.tool(
    title="Split document",
    description=(
        "Split a multi-page document into several documents, following the "
        "mailbox's splitting settings (AI, keywords, page ranges or every N "
        "pages — at least one must be enabled). Asynchronous: returns a "
        "notification_set (messages keyed by info / success / warning / error)."
    ),
    annotations=WRITE,
    structured_output=True,
)
def split_document(document_id: DocumentId) -> Dict[str, Any]:
    return Document.split(document_id)


@mcp.tool(
    title="Reverse split document",
    description=(
        "Undo a previous split of a document (valid only on a document that was "
        "split). Asynchronous: returns a notification_set (messages keyed by "
        "info / success / warning / error)."
    ),
    annotations=WRITE,
    structured_output=True,
)
def reverse_split_document(document_id: DocumentId) -> Dict[str, Any]:
    return Document.reverse_split(document_id)


@mcp.tool(
    title="Delete document",
    description=(
        "Permanently delete a document. This cannot be undone; confirm with the "
        "user first."
    ),
    annotations=DESTRUCTIVE,
    structured_output=True,
)
def delete_document(document_id: DocumentId) -> Dict[str, Any]:
    Document.delete(document_id)
    return {"deleted": True, "document_id": document_id}


FILE_PATH_DESC = (
    "Absolute path to the document on the machine running this MCP server "
    "(when launched locally by the desktop app, that is your own machine). "
    "~ is expanded. Do not base64-encode the file — just give its path."
)


@mcp.tool(
    title="Upload file",
    description=(
        "Upload a document file to a mailbox for parsing. Pass the file's path; "
        "the server reads it directly (no base64). The file must be on the "
        "machine running the server. Returns immediately with the new document "
        "id; parsing is asynchronous, so use upload_file_and_wait instead if "
        "you want the parsed result back."
    ),
    annotations=WRITE,
    structured_output=True,
)
def upload_file(
    mailbox_id: MailboxId,
    file_path: Annotated[str, Field(description=FILE_PATH_DESC)],
) -> Dict[str, Any]:
    return Document.upload_file(mailbox_id, file_path)


@mcp.tool(
    title="Upload text/email",
    description=(
        "Upload email or text content to a mailbox by its email address, "
        "creating a new document for parsing. Parsing is asynchronous; use "
        "upload_text_and_wait if you want the parsed result back."
    ),
    annotations=WRITE,
    structured_output=True,
)
def upload_text(
    recipient: Annotated[
        str, Field(description="The destination mailbox email address.")
    ],
    subject: Annotated[str, Field(description="Subject line of the document.")],
    sender: Annotated[
        Optional[str], Field(description="Optional sender email address.")
    ] = None,
    body_html: Annotated[
        Optional[str], Field(description="Optional HTML body.")
    ] = None,
    body_plain: Annotated[
        Optional[str], Field(description="Optional plain-text body.")
    ] = None,
) -> Dict[str, Any]:
    return Document.upload_text(
        recipient=recipient,
        subject=subject,
        sender=sender,
        body_html=body_html,
        body_plain=body_plain,
    )


# The synchronous tools poll every 5s for up to 10 minutes (fixed).
WAIT_DESC_SUFFIX = (
    " Polls every 5 seconds for up to 10 minutes; errors if the document is "
    "still being processed after that."
)


@mcp.tool(
    title="Wait for document",
    description=(
        f"Poll a document until it reaches a final status (any of "
        f"{FINAL_STATUS_LIST}). A document is still pending while "
        f"{PENDING_STATUS_LIST}." + WAIT_DESC_SUFFIX
    ),
    annotations=READ_ONLY,
    structured_output=True,
)
def wait_for_document(document_id: DocumentId) -> Dict[str, Any]:
    return Document.wait(document_id)


@mcp.tool(
    title="Upload file and wait",
    description=(
        "Upload a document file (by path) and block until it finishes "
        "processing, returning the parsed document." + WAIT_DESC_SUFFIX
    ),
    annotations=WRITE,
    structured_output=True,
)
def upload_file_and_wait(
    mailbox_id: MailboxId,
    file_path: Annotated[str, Field(description=FILE_PATH_DESC)],
) -> Dict[str, Any]:
    return Document.upload_file_and_wait(mailbox_id, file_path)


@mcp.tool(
    title="Upload text/email and wait",
    description=(
        "Upload email or text content and block until the document finishes "
        "processing, returning the parsed document." + WAIT_DESC_SUFFIX
    ),
    annotations=WRITE,
    structured_output=True,
)
def upload_text_and_wait(
    recipient: Annotated[
        str, Field(description="The destination mailbox email address.")
    ],
    subject: Annotated[str, Field(description="Subject line of the document.")],
    sender: Annotated[
        Optional[str], Field(description="Optional sender email address.")
    ] = None,
    body_html: Annotated[
        Optional[str], Field(description="Optional HTML body.")
    ] = None,
    body_plain: Annotated[
        Optional[str], Field(description="Optional plain-text body.")
    ] = None,
) -> Dict[str, Any]:
    return Document.upload_text_and_wait(
        recipient,
        subject,
        sender=sender,
        body_html=body_html,
        body_plain=body_plain,
    )


# ------------------------
# Webhook tools
# ------------------------


@mcp.tool(
    title="List webhooks",
    description="List all custom webhooks registered on the account.",
    annotations=READ_ONLY,
    structured_output=True,
)
def list_webhooks() -> List[Dict[str, Any]]:
    return Webhook.list()


@mcp.tool(
    title="Get webhook",
    description="Get the details of a single webhook by its id.",
    annotations=READ_ONLY,
    structured_output=True,
)
def get_webhook(webhook_id: WebhookId) -> Dict[str, Any]:
    return Webhook.retrieve(webhook_id)


@mcp.tool(
    title="Create webhook",
    description=(
        "Create a custom webhook. Use mailbox_id for document.* events and "
        "table_field_id for table.* events."
    ),
    annotations=WRITE,
    structured_output=True,
)
def create_webhook(
    event: Annotated[
        str,
        Field(
            description=(
                "Event type. One of: document.processed, "
                "document.processed.flattened, document.template_needed, "
                "document.export_failed, table.processed, "
                "table.processed.flattened."
            )
        ),
    ],
    target_url: Annotated[
        str, Field(description="URL that will receive the webhook POST requests.")
    ],
    mailbox_id: Annotated[
        Optional[int],
        Field(description="Mailbox id (required for document.* events)."),
    ] = None,
    table_field_id: Annotated[
        Optional[str],
        Field(
            description='Table field id like "PF12345" (required for table.* events).'
        ),
    ] = None,
    headers: Annotated[
        Optional[Dict[str, str]],
        Field(description="Optional custom HTTP headers to send with each POST."),
    ] = None,
    name: Annotated[
        Optional[str], Field(description="Optional name for the webhook.")
    ] = None,
) -> Dict[str, Any]:
    return Webhook.create(
        event=ParseurEvent(event),
        target_url=target_url,
        mailbox_id=mailbox_id,
        table_field_id=table_field_id,
        headers=headers,
        name=name,
    )


@mcp.tool(
    title="Delete webhook",
    description=(
        "Permanently delete a webhook by its id. This cannot be undone; confirm "
        "with the user first."
    ),
    annotations=DESTRUCTIVE,
    structured_output=True,
)
def delete_webhook(webhook_id: WebhookId) -> Dict[str, Any]:
    Webhook.delete(webhook_id)
    return {"deleted": True, "webhook_id": webhook_id}


@mcp.tool(
    title="Enable webhook",
    description="Enable (attach) an existing webhook for a mailbox.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def enable_webhook(mailbox_id: MailboxId, webhook_id: WebhookId) -> Dict[str, Any]:
    return Webhook.enable(mailbox_id, webhook_id)


@mcp.tool(
    title="Pause webhook",
    description="Pause (detach) a webhook from a mailbox without deleting it.",
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def pause_webhook(mailbox_id: MailboxId, webhook_id: WebhookId) -> Dict[str, Any]:
    return Webhook.pause(mailbox_id, webhook_id)


# ------------------------
# Export config tools
# ------------------------

ExportConfigId = Annotated[
    int, Field(description="The integer id of the export configuration.")
]
EXPORT_TYPE_DESC = (
    "Export type. PARSER exports the document-level result; PARSER_FIELD "
    "exports a table field's rows (then parser_field_id is required)."
)
ITEMS_DESC = "Columns to export. Use list_export_fields to discover the valid items."


@mcp.tool(
    title="Get mailbox export",
    description=(
        "Get download links for ALL parsed results of a mailbox as one file "
        "(document-level export: one row per processed document, the mailbox's "
        "fields as columns). Returns self-authenticating csv_download / "
        "json_download / xls_download URLs — hand one to the user to download "
        "the file. For a single table field use get_table_export; for a custom "
        "column selection use create_export_config."
    ),
    annotations=READ_ONLY,
    structured_output=True,
)
def get_mailbox_export(mailbox_id: MailboxId) -> Dict[str, Any]:
    mailbox = Mailbox.retrieve(mailbox_id)
    return {
        "csv_download": mailbox.get("csv_download"),
        "json_download": mailbox.get("json_download"),
        "xls_download": mailbox.get("xls_download"),
    }


@mcp.tool(
    title="Get table export",
    description=(
        "Get download links for the rows of a table field as one file (one row "
        "per line item, the table columns as columns). Returns "
        "self-authenticating csv_download / json_download / xls_download URLs — "
        "hand one to the user to download the file. Use list_parser_fields to "
        "find the TABLE field's id."
    ),
    annotations=READ_ONLY,
    structured_output=True,
)
def get_table_export(mailbox_id: MailboxId, field_id: FieldId) -> Dict[str, Any]:
    field = next(
        (f for f in ParserField.list(mailbox_id) if f.get("id") == field_id), None
    )
    if field is None:
        raise ValueError(
            f"No parser field with id {field_id!r} in mailbox {mailbox_id}"
        )
    return {
        "csv_download": field.get("csv_download"),
        "json_download": field.get("json_download"),
        "xls_download": field.get("xls_download"),
    }


@mcp.tool(
    title="List export fields",
    description=(
        "List the groups of columns that can be exported for a mailbox: one for "
        "the document-level export (PARSER) and one per table field "
        "(PARSER_FIELD). Use the returned items to build an export config."
    ),
    annotations=READ_ONLY,
    structured_output=True,
)
def list_export_fields(mailbox_id: MailboxId) -> List[Dict[str, Any]]:
    return ExportConfig.available_fields(mailbox_id)


@mcp.tool(
    title="List export configs",
    description="List the export configurations of a mailbox.",
    annotations=READ_ONLY,
    structured_output=True,
)
def list_export_configs(mailbox_id: MailboxId) -> List[Dict[str, Any]]:
    return ExportConfig.list(mailbox_id)


@mcp.tool(
    title="Get export config",
    description=(
        "Get a single export configuration, including its csv_download / "
        "xls_download URLs."
    ),
    annotations=READ_ONLY,
    structured_output=True,
)
def get_export_config(
    mailbox_id: MailboxId, export_config_id: ExportConfigId
) -> Dict[str, Any]:
    return ExportConfig.retrieve(mailbox_id, export_config_id)


@mcp.tool(
    title="Create export config",
    description=(
        "Create an export configuration selecting which columns to export. "
        "Returns the config with csv_download / xls_download URLs."
    ),
    annotations=WRITE,
    structured_output=True,
)
def create_export_config(
    mailbox_id: MailboxId,
    name: Annotated[str, Field(description="Name of the export configuration.")],
    items: Annotated[List[str], Field(description=ITEMS_DESC)],
    export_type: Annotated[str, Field(description=EXPORT_TYPE_DESC)] = "PARSER",
    parser_field_id: Annotated[
        Optional[str],
        Field(description='Table field id (required for PARSER_FIELD), e.g. "PF1".'),
    ] = None,
) -> Dict[str, Any]:
    return ExportConfig.create(
        mailbox_id,
        name,
        items,
        export_type=export_type,
        parser_field_id=parser_field_id,
    )


@mcp.tool(
    title="Update export config",
    description=(
        "Update an export configuration. Only the provided fields are changed."
    ),
    annotations=WRITE_IDEMPOTENT,
    structured_output=True,
)
def update_export_config(
    mailbox_id: MailboxId,
    export_config_id: ExportConfigId,
    name: Annotated[
        Optional[str], Field(description="New name for the export configuration.")
    ] = None,
    items: Annotated[Optional[List[str]], Field(description=ITEMS_DESC)] = None,
) -> Dict[str, Any]:
    changes: Dict[str, Any] = {}
    if name is not None:
        changes["name"] = name
    if items is not None:
        changes["items"] = items
    return ExportConfig.update(mailbox_id, export_config_id, **changes)


@mcp.tool(
    title="Delete export config",
    description=(
        "Permanently delete an export configuration. Confirm with the user first."
    ),
    annotations=DESTRUCTIVE,
    structured_output=True,
)
def delete_export_config(
    mailbox_id: MailboxId, export_config_id: ExportConfigId
) -> Dict[str, Any]:
    ExportConfig.delete(mailbox_id, export_config_id)
    return {"deleted": True, "export_config_id": export_config_id}


INSTRUCTIONS = f"""\
Parseur extracts structured data from documents (PDFs, emails, scans, spreadsheets, ...). These tools manage a Parseur account end to end. A **mailbox** (a.k.a. parser) is the unit of work: it has extraction fields, receives documents, and produces structured results you can export or push via webhooks.

**IDs:** mailboxes and webhooks use an integer id; documents use a string id; parser/table fields use a `PF...` string id; export configs use an integer id.

## What you can do

Use these tools — don't assume a capability is missing, there is probably a tool for it.

- **Mailboxes:** `{list_mailboxes.__name__}` (search + sort), `{get_mailbox.__name__}`, `{create_mailbox.__name__}`, `{delete_mailbox.__name__}`. `{get_mailbox_schema.__name__}` returns the extracted fields and their types — call it to understand what a mailbox produces before listing results or building an export.
- **Mailbox settings:** one dedicated tool per setting — `{rename_mailbox.__name__}`, `{set_ai_engine.__name__}`, `{set_ai_instructions.__name__}`, `{set_email_processing.__name__}`, `{set_metadata.__name__}` (per-document columns), `{set_timezone.__name__}`, `{set_date_format.__name__}`, `{set_decimal_separator.__name__}`, `{set_allowed_extensions.__name__}` (Files to process), `{set_sender_filter.__name__}`; document splitting via `{split_by_ai.__name__}` / `{split_by_page.__name__}` / `{split_by_page_range.__name__}` / `{split_by_keywords.__name__}`; page processing via `{process_page_range.__name__}` / `{process_odd_pages.__name__}` / `{process_even_pages.__name__}`.
- **Fields:** `{list_parser_fields.__name__}`, `{add_parser_field.__name__}`, `{update_parser_field.__name__}`, `{delete_parser_field.__name__}`. A field has a name, a format (`TEXT`, `DATE`, `NUMBER`, `TABLE`, ...), optional AI instructions (`query`), an `is_required` flag, and an optional `choice_set` (allowed values). `TABLE` fields hold repeating line items (e.g. invoice rows).
- **Documents:** `{upload_file.__name__}` / `{upload_text.__name__}` to ingest; `{list_documents.__name__}` (search, sort, `received_after`/`received_before`, `with_result=true` to include parsed data), `{get_document.__name__}`, `{get_document_logs.__name__}` (processing history, useful to diagnose `{DocumentStatus.PARSEDKO.value}`/`{DocumentStatus.EXPORTKO.value}`), `{reprocess_document.__name__}` (re-run parsing, e.g. after editing fields), `{skip_document.__name__}`, `{copy_document.__name__}` (into another mailbox), `{delete_document.__name__}`.
- **Exports (files):** `{get_mailbox_export.__name__}`, `{get_table_export.__name__}`, `{list_export_fields.__name__}`, `{list_export_configs.__name__}`, `{get_export_config.__name__}`, `{create_export_config.__name__}`, `{update_export_config.__name__}`, `{delete_export_config.__name__}`.
- **Webhooks (real-time push):** `{list_webhooks.__name__}`, `{get_webhook.__name__}`, `{create_webhook.__name__}`, `{enable_webhook.__name__}` (attach to a mailbox), `{pause_webhook.__name__}` (detach without deleting), `{delete_webhook.__name__}`.

## Typical workflow

1. **Create a mailbox** with just a title (`{create_mailbox.__name__}`). Do NOT define fields up front — Parseur auto-detects them from the first documents during its identification phase. Adjust them afterwards with `{add_parser_field.__name__}` / `{update_parser_field.__name__}` / `{delete_parser_field.__name__}`, then `{reprocess_document.__name__}` so existing documents pick up the change.
2. **Send documents** to parse: `{upload_file.__name__}` (a path on the server's machine) or `{upload_text.__name__}` (email/HTML content sent to the mailbox address).
3. **Parsing is asynchronous.** A document is pending while its status is one of {PENDING_STATUS_LIST}, and final once it is anything else ({FINAL_STATUS_LIST}). `{DocumentStatus.PARSEDOK.value}` means success; the failure statuses are {FAILED_STATUS_LIST} — inspect `{get_document_logs.__name__}`. The extracted data lives in the document's `result` field, populated only once it reaches `{DocumentStatus.PARSEDOK.value}`. To get the result in a single call prefer `{upload_file_and_wait.__name__}` / `{upload_text_and_wait.__name__}`; to wait on an existing document use `{wait_for_document.__name__}`; then read `result` (or `{list_documents.__name__}` with `with_result=true`).
4. **Export the parsed data** as a file — three kinds of export:
   - Whole mailbox, one row per document: `{get_mailbox_export.__name__}`.
   - One table field, one row per line item: `{get_table_export.__name__}`.
   - A custom column selection: `{list_export_fields.__name__}` to discover the available columns, then `{create_export_config.__name__}`.

   Each returns ready-to-use csv / json / xlsx download links that are self-authenticating (the URL itself grants access) — hand the link to the user to download the file.
5. **React in real time** instead of polling: `{create_webhook.__name__}` (`document.*` events need a `mailbox_id`; `table.*` events need a `table_field_id`) and `{enable_webhook.__name__}` to attach it to a mailbox.

## Tips

- **Resolve names to ids first:** when the user names a mailbox, field, or webhook, call the matching listing tool (`{list_mailboxes.__name__}`, `{list_parser_fields.__name__}`, `{list_documents.__name__}`, `{list_webhooks.__name__}`, `{list_export_configs.__name__}`) to find its id before acting.
- The listing tools (`{list_mailboxes.__name__}`, `{list_documents.__name__}`, `{list_export_configs.__name__}`, `{list_webhooks.__name__}`) handle pagination and accept search/sort filters — use them instead of fetching everything and filtering yourself.

## Safety

Read-only tools never modify data and are safe to call freely. The destructive tools — `{delete_mailbox.__name__}`, `{delete_parser_field.__name__}`, `{delete_document.__name__}`, `{delete_webhook.__name__}`, `{delete_export_config.__name__}` — permanently remove data, so confirm with the user first.
"""


def main() -> None:
    """Entry point for the ``parseur mcp`` command and ``parseur-mcp`` script."""
    ensure_api_key()
    mcp.run()


if __name__ == "__main__":
    main()
