from enum import Enum

from marshmallow import RAISE, fields, validate

from parseur.schemas import BaseSchema


class FieldFormat(str, Enum):
    """
    Enumeration of the data formats a parser field can have.

    Used as the ``format`` of a field when creating or updating a mailbox's
    fields (``parser_object_set``).
    """

    TEXT = "TEXT"
    ONELINE = "ONELINE"
    DATE = "DATE"
    TIME = "TIME"
    DATETIME = "DATETIME"
    NUMBER = "NUMBER"
    NAME = "NAME"
    ADDRESS = "ADDRESS"
    TABLE = "TABLE"
    LINK = "LINK"


class TableFieldReadSchema(BaseSchema):
    """A table field as summarised in a mailbox's ``table_set`` (id + name)."""

    id = fields.String(required=True)
    name = fields.String(required=True)


class ParserFieldBaseSchema(BaseSchema):
    """
    Properties shared by the read and write representations of a parser field.

    Both serializing API responses and validating create/update request bodies
    rely on these common fields, so they are declared once here.
    """

    name = fields.String(required=True)
    format = fields.String(
        required=True,
        validate=validate.OneOf(
            [e.value for e in FieldFormat],
            error="Must be one of: " + ", ".join(e.value for e in FieldFormat) + ".",
        ),
    )
    query = fields.String(allow_none=True)
    choice_set = fields.List(fields.String(), allow_none=True)


class ParserFieldReadSchema(ParserFieldBaseSchema):
    """Read schema for a parser field returned by the API."""

    id = fields.String(required=True)
    type = fields.String(required=True)
    is_required = fields.Boolean(required=True)
    used_by_ai = fields.Boolean(required=True)

    csv_download = fields.String(required=True)
    json_download = fields.String(required=True)
    xls_download = fields.String(required=True)

    parser_object_set = fields.List(fields.Nested("ParserFieldReadSchema"))


class ParserFieldWriteSchema(ParserFieldBaseSchema):
    """
    Write schema for a parser field.

    Used to validate and serialize each entry of a mailbox's
    ``parser_object_set``. Unknown fields are rejected so read-only properties
    (``type``, ``csv_download``, ...) and typos never reach the API silently.
    Pass ``id`` to update an existing field; omit it to create a new one.
    """

    class Meta:
        unknown = RAISE
        ordered = True

    # Present when updating an existing field, omitted when creating one.
    id = fields.String()
    is_required = fields.Boolean()
    used_by_ai = fields.Boolean()
    # Set to True to delete this field (matched by name) on the next save.
    _destroy = fields.Boolean()
    # Nested columns, used when ``format`` is TABLE.
    parser_object_set = fields.Nested(
        "ParserFieldWriteSchema", many=True, allow_none=True
    )
