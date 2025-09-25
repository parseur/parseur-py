from marshmallow import fields, validate

from parseur.schemas import BaseSchema
from parseur.schemas.document import DocumentStatus
from parseur.schemas.paserfield import ParserFieldSchema, TableFieldSchema
from parseur.schemas.webhook import WebhookSchema


class PageRangeSchema(BaseSchema):
    start_index = fields.Int(required=True)
    end_index = fields.Int(allow_none=True)


class SplitKeyWordsSchema(BaseSchema):
    is_before = fields.Boolean(required=True)
    keyword = fields.String(required=True)


class MailboxSchema(BaseSchema):
    id = fields.Int(required=True)
    name = fields.String(required=True)
    email_prefix = fields.String(required=True)
    account_uuid = fields.String(required=True)
    ai_engine = fields.String(required=True)
    secret = fields.String(allow_none=True)

    # ################
    # Basic settings #
    # ################
    decimal_separator = fields.String(
        allow_none=True,
        validate=validate.OneOf([".", ","], error="Must be '.' or ',' or null."),
    )
    default_timezone = fields.String(allow_none=True)

    # Input date format for parsing dates. Accepts "MONTH_FIRST", "DAY_FIRST", or None.
    #   MONTH_FIRST: mm/dd/yyyy, mm-dd-yyyy
    #   DAY_FIRST: dd/mm/yyyy, dd-mm-yyyy
    input_date_format = fields.String(
        allow_none=True,
        validate=validate.OneOf(
            ["MONTH_FIRST", "DAY_FIRST"],
            error="Must be 'MONTH_FIRST', 'DAY_FIRST', or null.",
        ),
    )
    # Parseur will automatically delete documents once they get older than the selected threshold.
    retention_policy = fields.Int(allow_none=True)

    # ###################
    # Advanced settings #
    # ###################

    # List of allowed file extensions for document processing.
    #   Example: ["pdf", "docx", "png"]
    allowed_extensions = fields.List(fields.String(), allow_none=True)

    # Force use of OCR on PDFs. Enable if data is garbled or text is in images.
    # Reprocess documents after enabling. May slow down processing.
    force_ocr = fields.Boolean(allow_none=True)

    # Expand field names in JSON Result.
    # Example: "user.name": "John" -> {"user": {"name": "John"}}.
    expand_result = fields.Boolean(allow_none=True)

    # Disable links on documents. Useful for manual data entry.
    disable_document_links = fields.Boolean(allow_none=True)

    # Disable the deskew algorithm if it creates a staircase effect when straightening.
    disable_deskew = fields.Boolean(allow_none=True)

    # Extract XML from HTML comments into separate documents.
    extract_xml_from_comment = fields.Boolean(allow_none=True)

    # Email sender block/allow list.
    #   True = allowlist mode (only allow listed senders).
    #   False = blocklist mode (block listed senders).
    use_whitelist_instead_of_blacklist = fields.Boolean(allow_none=True)
    emails_or_domains = fields.List(fields.String(), allow_none=True)

    # Email processing: process emails and attachments.
    process_attachments = fields.Boolean(required=True)

    # Email processing: process attachments only. Skip emails.
    attachments_only = fields.Boolean(required=True)

    # Page processing: only even pages (2, 4, 6, ...)
    even_pages = fields.Boolean(required=True)
    # Page processing: only odd pages (1, 3, 5, ...)
    odd_pages = fields.Boolean(required=True)
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

    # Metadata fields
    attachments_field = fields.Boolean(required=True)
    bcc_field = fields.Boolean(required=True)
    cc_field = fields.Boolean(required=True)
    content_field = fields.Boolean(required=True)
    credit_count_field = fields.Boolean(required=True)
    document_id_field = fields.Boolean(required=True)
    document_url_field = fields.Boolean(required=True)
    headers_field = fields.Boolean(required=True)
    html_document_field = fields.Boolean(required=True)
    last_reply_field = fields.Boolean(required=True)
    mailbox_id_field = fields.Boolean(required=True)
    original_document_field = fields.Boolean(required=True)
    original_recipient_field = fields.Boolean(required=True)
    page_count_field = fields.Boolean(required=True)
    parsing_engine_field = fields.Boolean(required=True)
    processed_date_field = fields.Boolean(required=True)
    processed_field = fields.Boolean(required=True)
    processed_time_field = fields.Boolean(required=True)
    public_document_url_field = fields.Boolean(required=True)
    received_date_field = fields.Boolean(required=True)
    received_field = fields.Boolean(required=True)
    received_time_field = fields.Boolean(required=True)
    recipient_field = fields.Boolean(required=True)
    recipient_suffix_field = fields.Boolean(required=True)
    reply_to_field = fields.Boolean(required=True)
    searchable_pdf_field = fields.Boolean(required=True)
    sender_field = fields.Boolean(required=True)
    sender_name_field = fields.Boolean(required=True)
    split_page_range_field = fields.Boolean(required=True)
    subject_field = fields.Boolean(required=True)
    template_field = fields.Boolean(required=True)
    text_document_field = fields.Boolean(required=True)
    to_field = fields.Boolean(required=True)

    # Webhooks
    available_webhook_set = fields.List(fields.Nested(WebhookSchema), required=True)
    webhook_set = fields.List(fields.Nested(WebhookSchema), required=True)

    # Parser and tables fields
    table_set = fields.List(fields.Nested(TableFieldSchema))
    parser_object_set = fields.List(fields.Nested(ParserFieldSchema))
