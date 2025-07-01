from marshmallow import fields

from parseur.schemas import BaseSchema


class ParserFieldSchema(BaseSchema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    format = fields.String(required=True)
    type = fields.String(required=True)

    is_optional = fields.Boolean(allow_none=True)
    query = fields.String(allow_none=True)

    csv_download = fields.String(required=True)
    json_download = fields.String(required=True)
    xls_download = fields.String(required=True)

    parser_object_set = fields.List(fields.Nested("ParserFieldSchema"))


class TableFieldSchema(BaseSchema):
    id = fields.String(required=True)
    name = fields.String(required=True)
