from marshmallow import fields, post_load, validate

from parseur.event import ParseurEvent
from parseur.schemas import BaseSchema


class WebhookSchema(BaseSchema):
    id = fields.Int(required=True)
    category = fields.String(required=True)
    event = fields.String(
        required=True,
        validate=validate.OneOf([e.value for e in ParseurEvent]),
    )
    target = fields.URL(required=True)
    name = fields.String(allow_none=True)
    headers = fields.Dict(keys=fields.String(), values=fields.String(), allow_none=True)

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
