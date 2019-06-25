import pytest
import mock

from picli import config


@pytest.fixture
def style_stage_deps():
    style_deps = ["validate"]

    return style_deps


@pytest.fixture
def validate_stage_deps_circular():
    validate_deps_circular = ["style"]

    return validate_deps_circular


@pytest.fixture
def style_stage_deps_circular():
    style_deps_circular = ["style"]

    return style_deps_circular


@pytest.fixture
def style_stage_fixture(deps=style_stage_deps()):
    style_stage = {
        "name": "style",
        "deps": deps,
        "resources": [{"name": "flake8", "uri": "/flake8_v1.1"}],
        "config": [{"files": "*.py", "resource": "flake8"}],
    }

    return style_stage


@pytest.fixture
def validate_stage_fixture(deps=None):
    validate_stage = {
        "name": "validate",
        "deps": deps,
        "resources": [{"name": "validation", "uri": "/validation_v1.1"}],
        "config": [{"files": "*", "resource": "validation"}],
    }

    return validate_stage


@pytest.fixture
def build_stage_fixture():
    build_stage = {
        "name": "build",
        "deps": ["validate", "style"],
        "resources": [{"name": "ansiblerunner", "uri": "/ansiblerunner_v1.1"}],
        "config": [{"files": "*", "resource": "ansiblerunner"}],
    }

    return build_stage


@pytest.fixture
def default_stage_fixture():
    default_stage = {
        "name": "default",
        "deps": [],
        "resources": [{"name": "default", "uri": "/default"}],
        "config": [{"files": "*", "resource": "default"}],
    }

    return default_stage


@pytest.fixture
def default_stages_fixture(style_stage_fixture, build_stage_fixture):
    stages = {
        "stages": [style_stage_fixture, validate_stage_fixture(), build_stage_fixture]
    }

    return stages


@pytest.fixture(
    params=[
        [
            style_stage_fixture(),
            validate_stage_fixture(deps=validate_stage_deps_circular()),
            build_stage_fixture(),
        ],
        [
            style_stage_fixture(deps=style_stage_deps_circular()),
            validate_stage_fixture(),
            build_stage_fixture(),
        ],
    ]
)
def circular_stages_fixture(request):
    stages = {"stages": request.param}

    return stages


@pytest.fixture
def gman_events_fixture():

    gman_events = [
        {
            "message": "blank message",
            "status": "started",
            "thread_id": "",
            "timestamp": "2019-05-16T19:56:33.231452+00:00",
            "task": {
                "project": "python_project",
                "run_id": "574b1db2-ae55-41bb-8680-43703f3031f2",
                "caller": "gateway",
                "task_id": "157dee55-819b-4706-8809-f5642ac035e6",
            },
        }
    ]

    return gman_events


@pytest.fixture
def default_config_fixture():

    config = {
        "project_name": "python_project",
        "version": "0.0.0",
        "gman_url": "http://172.17.0.1:8089/gman",
        "faas_endpoint": "http://172.17.0.1:8000",
        "storage": {
            "type": "minio",
            "hostname": "172.17.0.1:9000",
            "access_key": "blah",
            "secret_key": "blah",
        },
    }

    return config


@pytest.fixture
def patched_logger_critical(mocker):
    return mocker.patch("logging.Logger.critical")


@pytest.fixture
def patched_logger_info(mocker):
    return mocker.patch("logging.Logger.info")


@pytest.fixture
def baseconfig_patches(mocker):
    mocker.patch("picli.config.BaseConfig._write_state_file")
    mocker.patch("picli.config.BaseConfig._create_state_file")


@pytest.fixture
def default_read_patches(mocker, default_config_fixture, default_stages_fixture):
    mocker.patch(
        "picli.config.BaseConfig.read_stage_defs",
        return_value=default_stages_fixture["stages"],
    )
    mocker.patch(
        "picli.config.BaseConfig._read_config", return_value=default_config_fixture
    )


@pytest.fixture
def default_stage_execute_patches(mocker):
    mocker.patch("picli.stage.Stage._is_dependent_stage_state_completed")
    mocker.patch("picli.config.BaseConfig.update_state")
    mocker.patch("picli.stage.Stage._create_project_artifact")
    mocker.patch("picli.stage.Stage._submit_job")
    mocker.patch("picli.stage.Stage._check_thread_status")
    mocker.patch(
        "piperci.gman.client.request_new_task_id",
        return_value={"task": {"task_id": "1234"}},
    )


@pytest.fixture
def default_stage_create_project_patches(mocker):
    mocker.patch("picli.stage.generate_sri", return_value="1234")
    mocker.patch("picli.stage.hash_to_urlsafeb64")
    mocker.patch("picli.stage.os.path.basename")
    mocker.patch("picli.stage.Stage._zip_project", return_value=mock.Mock())


@pytest.fixture
def config_instance(mocker, default_stages_fixture, default_config_fixture):
    mocker.patch(
        "picli.config.BaseConfig.read_stage_defs",
        return_value=default_stages_fixture["stages"],
    )
    mocker.patch(
        "picli.config.BaseConfig._read_config", return_value=default_config_fixture
    )
    mocker.patch("picli.config.BaseConfig._write_state_file")
    mocker.patch("picli.config.BaseConfig._create_state_file")
    c = config.BaseConfig("blah", debug=False)
    return c


@pytest.fixture
def dummy_controller_response():
    task = {
        "task": {
            "caller": "picli",
            "thread_id": "1234",
            "run_id": "94944f48-6d92-49ba-aee3-72bb6e729c38",
            "task_id": "1234",
            "project": "python_project",
        },
        "status": "started",
        "event_id": "80b78fb7-b00a-4dba-bdf0-f716678b5f66",
        "message": "Requesting new taskID",
        "timestamp": "2019-06-19T13:38:05.758470+00:00",
    }

    return task