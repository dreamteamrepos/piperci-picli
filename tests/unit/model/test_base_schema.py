from picli.model import base_schema


def test_validate_success(default_config_fixture):
    assert not base_schema.validate(default_config_fixture)


def test_validate_fails():
    schema = {}
    assert base_schema.validate(schema)
