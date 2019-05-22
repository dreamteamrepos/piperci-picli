import mock
import pytest

from picli import config
from picli.stage import Stage


def test_get_run_id_reads_state(mocker, config_instance):
    expected_run_id = "1234"
    mocker.patch("picli.util.safe_load_file", return_value={"run_id": "1234"})
    config_instance.clean_state = False
    run_id = config_instance._get_run_id()
    assert run_id == expected_run_id


def test_get_run_id_calls_generate_when_clean(mocker, config_instance):
    mock_generate_run_id = mocker.patch("picli.config.BaseConfig._generate_run_id")
    config_instance.clean_state = True
    config_instance._get_run_id()
    assert mock_generate_run_id.called_once()


@pytest.mark.usefixtures("baseconfig_patches", "default_read_patches")
def test_config_instance_calls_clean(mocker):
    mock_clean = mocker.patch("picli.config.BaseConfig._clean_state", mock.MagicMock())
    c = config.BaseConfig("blah", clean_state=True, debug=False)
    mock_clean.assert_called_once()


@pytest.mark.usefixtures("baseconfig_patches", "default_read_patches")
def test_config_instance_clean_resets_state_property(mocker):
    mocker.patch("shutil.rmtree")
    mocker.patch("picli.config.BaseConfig._create_state_file")
    c = config.BaseConfig("blah", clean_state=True, debug=False)
    c.state = {"reset_me": "please"}
    c._clean_state()
    assert [*c.state] == []


@pytest.mark.usefixtures("baseconfig_patches", "default_read_patches")
def test_config_instance_reads_config(mocker):
    mock_read_state = mocker.patch("picli.config.BaseConfig.read_state_file")
    mocker.patch("picli.config.BaseConfig._get_run_id")
    c = config.BaseConfig("blah", clean_state=False, debug=False)
    mock_read_state.assert_called_once()


@pytest.mark.usefixtures("baseconfig_patches", "default_read_patches")
def test_config_instance_reads_run_id(mocker):
    run_id = {"run_id": "1234"}
    mock_load_state = mocker.patch("picli.util.safe_load_file", return_value=run_id)
    mocker.patch("picli.config.BaseConfig.read_state_file")
    c = config.BaseConfig("blah", clean_state=False, debug=False)
    mock_load_state.assert_called_once()
    assert c.run_id == "1234"


@pytest.mark.usefixtures("baseconfig_patches", "default_read_patches")
def test_config_instance_invalid_state_file(mocker):
    invalid_state_file = {"no_run_id": "1234"}
    run_id = "1234"
    mock_generate = mocker.patch("picli.util.generate_run_id", return_value=run_id)
    mock_clean_state = mocker.patch("picli.config.BaseConfig._clean_state")
    mocker.patch("picli.util.safe_load_file", return_value=invalid_state_file)
    c = config.BaseConfig("blah", clean_state=False, debug=False)
    mock_generate.assert_called_once()
    mock_clean_state.assert_called_once()
    assert c.run_id == "1234"


@pytest.mark.usefixtures("baseconfig_patches")
def test_read_stage_defs_reads_stages_file(mocker, default_config_fixture):
    mocker.patch(
        "picli.config.BaseConfig._read_config", return_value=default_config_fixture
    )
    mocker.patch("picli.config.BaseConfig.read_state_file", return_value={})
    mocker.patch("picli.config.BaseConfig._get_run_id", return_value=True)
    mock_load_file = mocker.patch("picli.config.util.safe_load_file")
    c = config.BaseConfig("blah", debug=False)
    c.read_stage_defs()
    args, kwargs = mock_load_file.call_args
    assert "blah/stages.yml" in args


@pytest.mark.usefixtures("baseconfig_patches")
def test_read_config_reads_config_file(mocker, default_stages_fixture):
    mocker.patch(
        "picli.config.BaseConfig.read_stage_defs",
        return_value=default_stages_fixture["stages"],
    )
    mocker.patch("picli.config.BaseConfig.read_state_file", return_value={})
    mocker.patch("picli.config.BaseConfig._init_storage_client")
    mocker.patch("picli.config.BaseConfig._validate")
    mock_load_file = mocker.patch("picli.config.util.safe_load_file")
    c = config.BaseConfig("blah", debug=False)
    c._read_config()
    args, kwargs = mock_load_file.call_args
    assert "blah/config.yml" in args


def test_validate_calls_sysexit_with_errors(mocker, config_instance):
    mocker.patch("picli.config.base_schema.validate", mock.MagicMock())
    with pytest.raises(SystemExit):
        config_instance._validate()


def test_piedpiper_dir_returns_directory(mocker, config_instance):
    config_instance.base_path = "blah"
    mocker.patch("picli.config.os.path.isdir", return_value=True)
    assert config_instance.piedpiper_dir == "blah/piedpiper.d"


def test_piedpiper_dir_calls_sysexit_on_error(config_instance):
    config_instance.base_path = "fail"
    with pytest.raises(SystemExit):
        config_instance.piedpiper_dir


@pytest.mark.usefixtures("baseconfig_patches")
def test_read_stage_defs_returns_stages(
    mocker, default_stages_fixture, default_config_fixture
):
    mocker.patch("picli.util.safe_load_file", return_value=default_stages_fixture)
    mocker.patch(
        "picli.config.BaseConfig._read_config", return_value=default_config_fixture
    )
    c = config.BaseConfig("blah", debug=False)
    assert c.read_stage_defs() == default_stages_fixture["stages"]


def test_get_sequence_returns_order(config_instance):
    expected_stages = ["validate", "style", "build"]

    assert (
        config_instance.get_sequence(stages=["validate", "style", "build"])
        == expected_stages
    )


def test_get_sequence_unordered(config_instance):
    expected_stages = ["validate", "style", "build"]

    assert config_instance.get_sequence(stages=["build", "validate"]) == expected_stages


def test_get_sequence_empty(config_instance):
    assert config_instance.get_sequence(stages=[]) == []


def test_get_sequence_default(config_instance):
    expected_stages = ["validate", "style", "build"]
    stages = [s.name for s in config_instance.stages]

    assert config_instance.get_sequence(stages=stages) == expected_stages


def test_get_sequence_no_stage(config_instance):
    with pytest.raises(SystemExit):
        config_instance.get_sequence(stages=["does-not-exist"])


@pytest.mark.usefixtures("baseconfig_patches")
def test_get_sequence_circular_dep(
    mocker, default_config_fixture, circular_stages_fixture
):
    mocker.patch(
        "picli.config.BaseConfig.read_stage_defs",
        return_value=circular_stages_fixture["stages"],
    )
    mocker.patch(
        "picli.config.BaseConfig._read_config", return_value=default_config_fixture
    )
    c = config.BaseConfig("blah", debug=False)
    stages = ["validate", "style", "build"]

    with pytest.raises(SystemExit):
        c.get_sequence(stages=stages)


def test_execute_calls_stage_execute(config_instance):
    stages = ["validate", "style", "build"]
    with mock.patch.object(Stage, "execute") as mock_execute:
        config_instance.execute(stages)
        mock_execute.assert_called()


def test_display_calls_stage_display(config_instance):
    stages = ["validate", "style", "build"]
    with mock.patch.object(Stage, "display") as mock_display:
        config_instance.display(stages, 2)
        mock_display.assert_called()
