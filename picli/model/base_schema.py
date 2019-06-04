from marshmallow import fields
from marshmallow import Schema
from marshmallow import RAISE
from marshmallow import ValidationError


class StorageSchema(Schema):
    url = fields.Str(required=True)
    access_key = fields.Str(required=True)
    secret_key = fields.Str(required=True)


class ConfigSchema(Schema):
    project_name = fields.Str(required=True)
    version = fields.Str(required=True)
    gman_url = fields.Str(required=True)
    faas_endpoint = fields.Str(required=True)
    storage = fields.Nested(StorageSchema)


def validate(config):
    schema = ConfigSchema(unknown=RAISE)
    try:
        _ = schema.load(config)
        result = None
    except ValidationError as err:
        result = err
    return result
