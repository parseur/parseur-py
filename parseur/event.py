from enum import Enum


class ParseurEvent(str, Enum):
    """
    Enumeration of supported Parseur webhook event types.

    Use these values when registering webhooks to specify which event to listen for.

    Members:

    - `DOCUMENT_PROCESSED`: Document processed successfully.
    - `DOCUMENT_PROCESSED_FLATTENED`: Document processed as flat data.
    - `DOCUMENT_TEMPLATE_NEEDED`: Document processing failed (template needed).
    - `DOCUMENT_EXPORT_FAILED`: Export of the document failed.
    - `TABLE_PROCESSED`: A table field row was processed.
    - `TABLE_PROCESSED_FLATTENED`: A table field row (flattened) was processed.
    """

    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_PROCESSED_FLATTENED = "document.processed.flattened"
    DOCUMENT_TEMPLATE_NEEDED = "document.template_needed"
    DOCUMENT_EXPORT_FAILED = "document.export_failed"
    TABLE_PROCESSED = "table.processed"
    TABLE_PROCESSED_FLATTENED = "table.processed.flattened"

    def is_table_event(self) -> bool:
        return self.value.startswith("table")
