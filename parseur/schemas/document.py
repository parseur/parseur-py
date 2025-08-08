from enum import Enum
import json

from marshmallow import fields, pre_load, validate

from parseur.schemas import BaseSchema


class DocumentStatus(str, Enum):
    """
    Enum for Parseur document processing statuses.
    """

    INCOMING = "INCOMING"  # the file has been received by our system
    ANALYZING = "ANALYZING"  # the file is being analyzed against import parameters and mailbox settings
    DELETED = "DELETED"  # the file has been deleted by the user
    PROGRESS = "PROGRESS"  # the file is currently being processed by the AI engine for the mailbox
    PARSEDOK = (
        "PARSEDOK"  # the file has been processed and data is available for export
    )
    PARSEDKO = "PARSEDKO"  # the processing for this file failed
    QUOTAEXC = "QUOTAEXC"  # processing was stopped because the user does not have enough credits
    SKIPPED = "SKIPPED"  # processing was skipped because of a template
    SPLIT = "SPLIT"  # the file has been split into multiple documents
    EXPORTKO = "EXPORTKO"  # exporting for this file failed
    TRANSKO = "TRANSKO"  # post-processing for this file failed
    INVALID = "INVALID"  # the imported file is not supported by our system


class DocumentSchema(BaseSchema):
    id = fields.Int(required=True)
    name = fields.String(required=True)

    status = fields.String(
        required=True,
        validate=validate.OneOf([e.value for e in DocumentStatus]),
    )
    status_source = fields.String(allow_none=True)

    received = fields.DateTime(required=True)
    processed = fields.DateTime(allow_none=True)

    ai_credits_used = fields.Int(required=True)
    credits_used = fields.Int(required=True)

    is_ai_ready = fields.Boolean(required=True)
    is_ocr_ready = fields.Boolean(required=True)
    is_processable = fields.Boolean(required=True)
    is_split = fields.Boolean(required=True)
    is_splittable = fields.Boolean(required=True)

    parser = fields.Int(required=True)
    template = fields.Int(allow_none=True)

    attached_to = fields.Int(allow_none=True)
    prev_id = fields.Int(allow_none=True)
    next_id = fields.Int(allow_none=True)

    content = fields.String(allow_none=True)
    result = fields.Raw(allow_none=True)

    csv_download_url = fields.URL(required=True)
    json_download_url = fields.URL(required=True)
    xls_download_url = fields.URL(required=True)

    original_document_url = fields.URL(required=True)
    ocr_ready_url = fields.URL(allow_none=True)

    @pre_load
    def parse_result_json(self, data, **kwargs):
        result = data.get("result")
        if result and isinstance(result, str):
            try:
                data["result"] = json.loads(result)
            except (TypeError, ValueError):
                pass
        return data


class DocumentLogSchema(BaseSchema):
    # Unique ID of the log entry
    id = fields.Integer(required=True)
    # Log event code (e.g., INCOMING)
    code = fields.String(required=True)
    # Creation timestamp in ISO format
    created = fields.DateTime(required=True)
    # Document ID
    document = fields.Integer(required=True)
    # Name of the document
    document_name = fields.String(required=True)
    # Human-readable log message
    message = fields.String(required=True)
    # Mailbox (parser) ID
    parser = fields.Integer(required=True)
    # Name of the mailbox
    parser_name = fields.String(required=True)
    # Optional JSON payload attached to the event
    payload = fields.Raw(allow_none=True)
    # Event source, typically 'DOCUMENT'
    source = fields.String(allow_none=True)
    # Status level, e.g. 'INFO', 'WARNING', 'ERROR'
    status = fields.String(required=True)
    # ID of the template involved, if any
    template = fields.Integer(allow_none=True)
    # Name of the template involved, if any
    template_name = fields.String(allow_none=True)

    @pre_load
    def parse_payload_json(self, data, **kwargs):
        payload = data.get("payload")
        if payload and isinstance(payload, str):
            try:
                data["payload"] = json.loads(payload)
            except (TypeError, ValueError):
                pass
        return data


class AttachmentSchema(BaseSchema):
    DocumentID = fields.String(required=True)
    name = fields.String(required=True)


class DocumentUploadSchema(BaseSchema):
    DocumentID = fields.String(allow_none=True)
    attachments = fields.List(fields.Nested(AttachmentSchema), allow_none=True)
    message = fields.String(required=True)
