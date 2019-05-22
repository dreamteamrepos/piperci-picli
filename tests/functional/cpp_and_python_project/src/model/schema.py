import marshmallow

from charon.model import base


class RequestSchema(base.Base):
    image_uuids = marshmallow.fields.List(marshmallow.fields.Str())
    source_project_id = marshmallow.fields.Str()
    dest_project_id = marshmallow.fields.Str()


class CloudSchema(base.Base):
    name = marshmallow.fields.Str()
    network_id = marshmallow.fields.Str()
    username = marshmallow.fields.Str()


class NotificationMattermostAuthenticationSchema(base.Base):
    access_token = marshmallow.fields.Str()


class NotificationMattermostSchema(base.Base):
    name = marshmallow.fields.Str()
    authentication = marshmallow.fields.Dict(
        values=marshmallow.fields.Nested(NotificationMattermostAuthenticationSchema)
    )
    url = marshmallow.fields.Str()
    verify = marshmallow.fields.Boolean()


class ScannerNessusAuthenticationSchema(base.Base):
    url = marshmallow.fields.Str()
    access_key = marshmallow.fields.Str()
    secret_key = marshmallow.fields.Str()


class ScannerNessusSchema(base.Base):
    name = marshmallow.fields.Str()
    compliance_threshold = marshmallow.fields.Str()
    authentication = marshmallow.fields.Dict(
        values=marshmallow.fields.Nested(ScannerNessusAuthenticationSchema)
    )
    verify = marshmallow.fields.Boolean()
    policy_id = marshmallow.fields.Str()


class CharonBaseSchema(base.Base):
    request = marshmallow.fields.Nested(RequestSchema)
    cloud = marshmallow.fields.Nested(CloudSchema)
    notification = marshmallow.fields.Nested(NotificationMattermostSchema)


class CharonNessusSchema(CharonBaseSchema):
    scanner = marshmallow.fields.Nested(ScannerNessusSchema)


class CharonMattermostSchema(CharonBaseSchema):
    notification = marshmallow.fields.Nested(NotificationMattermostSchema)


def validate(c):
    if c["scanner"]["name"] == "nessus":
        schema = CharonNessusSchema(strict=True)

    return schema.load(c)
