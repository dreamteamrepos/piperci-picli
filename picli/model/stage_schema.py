from marshmallow import fields
from marshmallow import Schema
from marshmallow import RAISE
from marshmallow import ValidationError


class ConfigSchema(Schema):
    resource = fields.Str(required=True)


class ResourceSchema(Schema):
    name = fields.Str(required=True)
    uri = fields.Str(Required=True)


class StageSchema(Schema):
    name = fields.Str(required=True)
    deps = fields.List(fields.Str(), required=True, allow_none=True)
    resources = fields.List(fields.Nested(ResourceSchema))
    config = fields.List(fields.Nested(ConfigSchema, unknown=True))


def validate(config):
    schema = StageSchema(unknown=RAISE)
    try:
        _ = schema.load(config)
        result = None
    except ValidationError as err:
        result = err
    return result
