from marshmallow import fields, post_load, pre_load, validate

from parseur.event import ParseurEvent
from parseur.schemas import BaseSchema


class WebhookSchema(BaseSchema):
    id = fields.Int(required=True)
    category = fields.String(required=True)
    event = fields.String(
        required=True,
        validate=validate.OneOf([e.value for e in ParseurEvent]),
    )
    target = fields.String(required=True)
    name = fields.String(allow_none=True)
    headers = fields.Dict(keys=fields.String(), values=fields.String(), allow_none=True)

    @pre_load
    def normalize_empty_fields(self, data, **kwargs):
        if "headers" in data and data["headers"] == "":
            data["headers"] = None
        if "name" in data and data["name"] == "":
            data["name"] = None
        return data

    @post_load
    def default_empty_headers(self, data, **kwargs):
        if data.get("headers") is None:
            data["headers"] = {}
        return data

    @post_load
    def default_empty_name(self, data, **kwargs):
        if data.get("name") is None:
            data["name"] = ""
        return data
