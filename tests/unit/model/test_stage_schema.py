from picli.model import stage_schema


def test_validate_success(default_stage_fixture):
    assert not stage_schema.validate(default_stage_fixture)


def test_validate_fails():
    schema = {}
    assert stage_schema.validate(schema)
