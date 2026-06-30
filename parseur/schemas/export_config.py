from enum import Enum

from marshmallow import RAISE, fields, validate

from parseur.schemas import BaseSchema


class ExportType(str, Enum):
    """
    Type of an export configuration.

    - ``PARSER``: export the document-level result (one row per document).
    - ``PARSER_FIELD``: export the rows of a table field.
    """

    PARSER = "PARSER"
    PARSER_FIELD = "PARSER_FIELD"


class ExportConfigReadSchema(BaseSchema):
    """Read schema for a mailbox export configuration."""

    id = fields.Int(required=True)
    name = fields.String(required=True)
    type = fields.String(required=True)
    parser_id = fields.Int(required=True)
    # Present only for a PARSER_FIELD (table) export config.
    parser_field_id = fields.String(allow_none=True)
    parser_field_name = fields.String(allow_none=True)
    # Columns included in the export.
    items = fields.List(fields.String(), required=True)
    # Download URLs for the configured export (resolved to absolute URLs).
    csv_download = fields.String(allow_none=True)
    xls_download = fields.String(allow_none=True)


class ExportConfigWriteSchema(BaseSchema):
    """
    Validate/serialize the body sent when creating or updating an export config.

    Unknown fields are rejected so read-only properties and typos never reach
    the API silently.
    """

    class Meta:
        unknown = RAISE
        ordered = True

    name = fields.String()
    type = fields.String(
        validate=validate.OneOf(
            [e.value for e in ExportType],
            error="Must be one of: " + ", ".join(e.value for e in ExportType) + ".",
        )
    )
    # Required when ``type`` is PARSER_FIELD; must be a table field id (e.g. "PF1").
    parser_field_id = fields.String(allow_none=True)
    items = fields.List(
        fields.String(),
        validate=validate.Length(min=1, error="items cannot be empty."),
    )
