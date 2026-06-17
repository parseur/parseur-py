from enum import Enum, IntFlag, auto

from marshmallow import RAISE, fields, validate

from parseur.schemas import BaseSchema


from parseur.schemas.document import DocumentStatus
from parseur.schemas.paserfield import (
    ParserFieldReadSchema,
    ParserFieldWriteSchema,
    TableFieldReadSchema,
)
from parseur.schemas.webhook import WebhookSchema

SUPPORTED_FILE_EXTENSIONS = frozenset(
    {
        "bmp",
        "csv",
        "doc",
        "docx",
        "eml",
        "gif",
        "html",
        "ics",
        "jpg",
        "mbox",
        "msg",
        "odp",
        "ods",
        "odt",
        "pdf",
        "png",
        "ppt",
        "pptx",
        "rtf",
        "tif",
        "txt",
        "xhtml",
        "xls",
        "xlsm",
        "xlsx",
        "xml",
        "zip",
    }
)


class Metadata(IntFlag):
    """Per-document metadata columns a mailbox can expose.

    A :class:`~enum.IntFlag`, so columns compose with ``|`` and can be enabled or
    disabled together (see :meth:`parseur.Mailbox.set_metadata`). Single source of
    truth for the ``*_field`` toggles: a member maps to its API field by
    lowercasing its name and appending ``_field`` (see :attr:`field`) — e.g.
    ``Metadata.SUBJECT`` -> ``"subject_field"``. Both the read and write mailbox
    schemas are derived from this enum so the column list lives in one place.
    """

    ATTACHMENTS = auto()
    BCC = auto()
    CC = auto()
    CONTENT = auto()
    CREATED_DATE = auto()
    CREATED = auto()
    CREATED_TIME = auto()
    CREDIT_COUNT = auto()
    DOCUMENT_ID = auto()
    DOCUMENT_URL = auto()
    HEADERS = auto()
    HTML_DOCUMENT = auto()
    LAST_REPLY = auto()
    MAILBOX_ID = auto()
    ORIGINAL_DOCUMENT = auto()
    ORIGINAL_RECIPIENT = auto()
    PAGE_COUNT = auto()
    PARSING_ENGINE = auto()
    PROCESSED_DATE = auto()
    PROCESSED = auto()
    PROCESSED_TIME = auto()
    PUBLIC_DOCUMENT_URL = auto()
    RECEIVED_DATE = auto()
    RECEIVED = auto()
    RECEIVED_TIME = auto()
    RECIPIENT = auto()
    RECIPIENT_SUFFIX = auto()
    REPLY_TO = auto()
    SEARCHABLE_PDF = auto()
    SENDER = auto()
    SENDER_NAME = auto()
    SPLIT_PAGE_RANGE = auto()
    SPLIT_PARENT_ID = auto()
    SUBJECT = auto()
    TEMPLATE = auto()
    TEXT_DOCUMENT = auto()
    TO = auto()

    @property
    def field(self) -> str:
        """The mailbox schema field this column maps to (e.g. ``subject_field``)."""
        return f"{self.name.lower()}_field"


# Read/write field mixins for the metadata columns, generated from Metadata so
# the column list is never repeated. Read keeps them lenient (server output);
# write exposes them as optional toggles.
MetadataReadFields = BaseSchema.from_dict(
    {meta.field: fields.Boolean(allow_none=True) for meta in Metadata},
    name="MetadataReadFields",
)
MetadataWriteFields = BaseSchema.from_dict(
    {meta.field: fields.Boolean() for meta in Metadata},
    name="MetadataWriteFields",
)


class AIEngine(str, Enum):
    """
    Enumeration of AI engines that can be set on a mailbox when creating or
    updating it.

    The values mirror the ``parser.ai_engine`` choices returned by the
    ``/bootstrap`` endpoint.

    Members:

    - `DISABLED`: No AI engine (template-based parsing only).
    - `GCP_AI_2_5`: AI Text engine v2.5 (analyzes extracted text).
    - `GCP_AI_3_TXT`: AI Text engine v3 (analyzes extracted text).
    - `GCP_AI_2`: AI Vision engine v3 (understands layout and images).
    """

    DISABLED = "DISABLED"
    GCP_AI_2_5 = "GCP_AI_2_5"
    GCP_AI_3_TXT = "GCP_AI_3_TXT"
    GCP_AI_2 = "GCP_AI_2"


class IdentificationStatus(str, Enum):
    """Identification status accepted when creating/updating a mailbox."""

    REQUESTED = "REQUESTED"
    PROGRESS = "PROGRESS"
    COMPLETED = "COMPLETED"
    MANUAL = "MANUAL"


class DateFormat(str, Enum):
    """How to read ambiguous dates in documents (the ``input_date_format``)."""

    MONTH_FIRST = "MONTH_FIRST"  # mm/dd/yyyy, mm-dd-yyyy, ...
    DAY_FIRST = "DAY_FIRST"  # dd/mm/yyyy, dd-mm-yyyy, ...


class DecimalSeparator(str, Enum):
    """Decimal separator for numbers in documents (the ``decimal_separator``)."""

    DOT = "."  # 123.45
    COMMA = ","  # 123,45


class PageRangeSchema(BaseSchema):
    start_index = fields.Int(required=True)
    end_index = fields.Int(allow_none=True)


class SplitKeyWordsSchema(BaseSchema):
    is_before = fields.Boolean(required=True)
    keyword = fields.String(required=True)


class MailboxBaseSchema(BaseSchema):
    """
    Mailbox settings shared by the read and write representations.

    These fields have the same definition whether a mailbox is read from the
    API or sent to it, so they are declared once here and inherited by both
    :class:`MailboxReadSchema` and :class:`MailboxWriteSchema`.
    """

    ai_instructions = fields.String(allow_none=True)

    decimal_separator = fields.String(
        allow_none=True,
        # "" kept for read leniency (a mailbox may report no override).
        validate=validate.OneOf(
            [e.value for e in DecimalSeparator] + [""],
            error="Must be '.', ',' or null.",
        ),
    )
    default_timezone = fields.String(allow_none=True)

    default_language = fields.String(allow_none=True)

    # Input date format for parsing dates. Accepts "MONTH_FIRST", "DAY_FIRST", or None.
    #   MONTH_FIRST: mm/dd/yyyy, mm-dd-yyyy
    #   DAY_FIRST: dd/mm/yyyy, dd-mm-yyyy
    input_date_format = fields.String(
        allow_none=True,
        validate=validate.OneOf(
            [e.value for e in DateFormat],
            error="Must be 'MONTH_FIRST', 'DAY_FIRST', or null.",
        ),
    )
    # Parseur will automatically delete documents once they get older than the selected threshold.
    retention_policy = fields.Int(allow_none=True)

    # List of allowed file extensions for document processing.
    #   Example: ["pdf", "docx", "png"]
    allowed_extensions = fields.List(fields.String(), allow_none=True)

    # Email sender block/allow list.
    #   True = allowlist mode (only allow listed senders).
    #   False = blocklist mode (block listed senders).
    use_whitelist_instead_of_blacklist = fields.Boolean(allow_none=True)
    emails_or_domains = fields.List(fields.String(), allow_none=True)

    # Page processing: only this page ranges. (same as split_page_range_set)
    page_range_set = fields.Nested(PageRangeSchema, allow_none=True, many=True)

    # Split documents every N pages.
    split_page = fields.Int(allow_none=True)
    # Split documents by page ranges.
    #   Example input: 1-5, 8, 11-13
    #   Enter ranges separated by commas. Use brackets to count from the end.
    #   E.g., (1) is last page. Example: 1, 2-(1) splits into two docs:
    #   - first page only
    #   - from page 2 to the end.
    split_page_range_set = fields.Nested(PageRangeSchema, allow_none=True, many=True)
    # Split documents by keywords.
    #   Enter the list of keywords to split on.
    #   Supports splitting before or after keywords.
    #   Keywords are case-sensitive.
    split_keywords = fields.Nested(SplitKeyWordsSchema, allow_none=True, many=True)


class MailboxReadSchema(MailboxBaseSchema, MetadataReadFields):
    """Schema for a mailbox as returned by the API."""

    id = fields.Int(required=True)
    name = fields.String(required=True)
    email_prefix = fields.String(required=True)
    account_uuid = fields.String(required=True)

    ai_engine = fields.String(required=True)
    # AI document splitting
    is_ai_split_enabled = fields.Boolean(allow_none=True)
    ai_split_instructions = fields.String(allow_none=True)

    # Email processing: process emails and attachments.
    process_attachments = fields.Boolean(required=True)
    # Email processing: process attachments only. Skip emails.
    attachments_only = fields.Boolean(required=True)

    # Page processing: only even pages (2, 4, 6, ...) / odd pages (1, 3, 5, ...)
    even_pages = fields.Boolean(required=True)
    odd_pages = fields.Boolean(required=True)

    # Counters
    document_count = fields.Int(allow_none=True)
    webhook_count = fields.Int(allow_none=True)
    template_count = fields.Int(allow_none=True)
    parser_object_count = fields.Int(allow_none=True)
    # Document per status count
    document_per_status_count = fields.Dict(
        keys=fields.String(validate=validate.OneOf([e.value for e in DocumentStatus])),
        values=fields.Int(),
        required=True,
    )

    # Last activity and modification timestamps
    last_activity = fields.DateTime(allow_none=True)
    template_set_last_modified = fields.DateTime(allow_none=True)
    parser_object_set_last_modified = fields.DateTime(allow_none=True)

    # URLs
    csv_download = fields.String(allow_none=True)
    json_download = fields.String(allow_none=True)
    xls_download = fields.String(allow_none=True)

    # Webhooks
    available_webhook_set = fields.List(fields.Nested(WebhookSchema), required=True)
    webhook_set = fields.List(fields.Nested(WebhookSchema), required=True)

    # Parser and tables fields
    table_set = fields.List(fields.Nested(TableFieldReadSchema))
    parser_object_set = fields.List(fields.Nested(ParserFieldReadSchema))


class MailboxWriteSchema(MailboxBaseSchema, MetadataWriteFields):
    """
    Schema describing the writable fields of a mailbox.

    Used to validate and serialize the request body sent when creating or
    updating a mailbox. Every field is optional, but unknown fields are
    rejected so that typos and read-only fields never reach the API silently.
    """

    class Meta:
        # Reject unknown fields instead of silently dropping them, so a
        # mistyped or read-only field raises a ValidationError.
        unknown = RAISE
        ordered = True

    name = fields.String()
    ai_engine = fields.String(
        validate=validate.OneOf(
            [e.value for e in AIEngine],
            error="Must be one of: " + ", ".join(e.value for e in AIEngine) + ".",
        )
    )
    identification_status = fields.String(
        validate=validate.OneOf([e.value for e in IdentificationStatus])
    )

    process_attachments = fields.Boolean()
    attachments_only = fields.Boolean()
    even_pages = fields.Boolean()
    odd_pages = fields.Boolean()

    # AI document splitting (the page-range / N-page / keyword split fields are
    # inherited as writable from MailboxBaseSchema).
    is_ai_split_enabled = fields.Boolean(allow_none=True)
    ai_split_instructions = fields.String(allow_none=True)

    # "Files to process": validated against the supported extensions on write
    allowed_extensions = fields.List(
        fields.String(validate=validate.OneOf(sorted(SUPPORTED_FILE_EXTENSIONS))),
        allow_none=True,
    )

    # Field definitions, validated against the writable field schema.
    parser_object_set = fields.Nested(
        ParserFieldWriteSchema, many=True, allow_none=True
    )


class MailboxCreateSchema(MailboxWriteSchema):
    """Validate/serialize the body of a ``POST /parser`` (create) request."""


class MailboxUpdateSchema(MailboxWriteSchema):
    """Validate/serialize the body of a ``PUT /parser/{id}`` (update) request."""

    id = fields.Int(required=True)
