import pytest
import mock
import logging
import os
import responses
import zipfile

from picli.config import BaseConfig
from picli.stage import Stage


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
def dependent_stage_fixture():
    dependent_stage = {
        "name": "dependent",
        "deps": ["default"],
        "resources": [{"name": "dependent", "uri": "/dependent"}],
        "config": [{"files": "*", "resource": "dependent"}],
    }
    return dependent_stage


@pytest.fixture()
def stages_fixture(default_stage_fixture, dependent_stage_fixture):
    stages = {"stages": [default_stage_fixture, dependent_stage_fixture]}
    return stages


@pytest.fixture
def stage_instance(default_stage_fixture, config_instance):
    stage = Stage(default_stage_fixture, config_instance)
    return stage


def test_stage_contains_config(stage_instance):
    assert isinstance(stage_instance.stage_config, BaseConfig)


def test_stage_name_is_style(stage_instance):
    assert stage_instance.name == "default"


def test_stage_logger_set_debug(mocker, default_stage_fixture, config_instance):
    mock_logger_set_level = mocker.patch("picli.stage.LOG.setLevel")
    config_instance.debug = True
    Stage(default_stage_fixture, config_instance)
    mock_logger_set_level.assert_called_with(logging.DEBUG)


def test_stage_can_add_dependencies(
    stage_instance, default_stage_fixture, config_instance
):
    stages = [Stage(default_stage_fixture, config_instance) for _ in range(1, 5)]
    for stage in stages:
        stage_instance.add_dependency(stage)

    assert all(isinstance(stage, Stage) for stage in stage_instance.dependencies)


def test_validate_calls_sysexit_with_errors(stage_instance):
    invalid_stage_def = {}
    with mock.patch("picli.stage.stage_schema.validate", mock.MagicMock()):
        with pytest.raises(SystemExit):
            stage_instance._validate(invalid_stage_def)


@pytest.mark.usefixtures("baseconfig_patches", "default_read_patches")
def test_dependent_stage_is_not_complete(mocker):
    c = BaseConfig("blah", debug=False)
    c.state = {"validate": {"state": "no"}}
    stage = next(stage for stage in c.stages if stage.name == "style")
    mocker.patch("picli.stage.Stage._check_task_status", return_value=False)
    assert not stage._is_dependent_stage_state_completed()


@pytest.mark.usefixtures("baseconfig_patches", "default_read_patches")
def test_dependent_stage_is_complete(mocker):
    c = BaseConfig("blah", debug=False)
    c.state = {"validate": {"state": "completed"}}
    stage = next(stage for stage in c.stages if stage.name == "style")
    mocker.patch("picli.stage.Stage._check_task_status", return_value=True)
    assert stage._is_dependent_stage_state_completed()


def test_check_task_status_updates_state(mocker, stage_instance):
    mocker.patch("picli.stage.util.wait_for_task_status", return_value=True)
    mocker.patch("picli.stage.util.update_task_id_status")
    with mock.patch("picli.config.BaseConfig.update_state") as mock_update_task_status:
        stage_instance._check_task_status("1234")
        mock_update_task_status.assert_called_once()


def test_check_task_status_failed(mocker, stage_instance):
    mocker.patch("picli.stage.util.wait_for_task_status", return_value=False)
    mocker.patch("picli.stage.util.update_task_id_status")
    mocker.patch("picli.stage.util.get_task_id_message", return_value={})
    mocker.patch("picli.config.BaseConfig.update_state")
    with pytest.raises(SystemExit):
        stage_instance._check_task_status("1234", "completed")


def test_submit_job_updates_gman(mocker, stage_instance):
    mocker.patch("picli.config.BaseConfig.update_state")
    mocker.patch("picli.stage.requests.post")
    with mock.patch("picli.stage.util.update_task_id_status") as mock_update:
        stage_instance._submit_job("resource", "artifacts", "task")
        mock_update.assert_called_once()


def test_submit_job_updates_state(mocker, stage_instance):
    mocker.patch("picli.stage.util.update_task_id_status")
    mocker.patch("picli.stage.requests.post")
    with mock.patch("picli.config.BaseConfig.update_state") as mock_update:
        stage_instance._submit_job("resource", "artifacts", "task")
        mock_update.assert_called_once()


@responses.activate
def test_submit_job_fails_with_500_updates_state(mocker, stage_instance):
    responses.add(responses.POST, "http://resource_url", status=500)
    mocker.patch("picli.stage.util.update_task_id_status")
    with mock.patch("picli.config.BaseConfig.update_state") as mock_update:
        with pytest.raises(SystemExit):
            stage_instance._submit_job("http://resource_url", "artifacts", "task")
        mock_update.assert_called_once()


@responses.activate
def test_submit_job_success_updates_gman(mocker, stage_instance):
    responses.add(responses.POST, "http://resource_url", status=200, json={})
    mocker.patch("picli.stage.util.update_task_id_status")
    with mock.patch("picli.stage.util.update_task_id_status") as mock_update:
        stage_instance._submit_job("http://resource_url", "artifacts", "task")
        mock_update.assert_called_once()


def test_display_downloads_artifact(mocker, stage_instance):
    mocker.patch("picli.config.Minio.list_objects", return_value=[mock.MagicMock()])
    mocker.patch("picli.stage.os.path.basename", return_value="blah")
    mocker.patch("picli.stage.Stage._check_task_status", return_value=True)
    mocker.patch("builtins.open", new_callable=mock.mock_open)
    mock_download = mocker.patch("picli.stage.util.download_artifact")
    stage_instance.stage_config.state = {
        "default": {"task_id": "blah"},
        "dependent": {"task_id": "blah"},
    }
    stage_instance.display()
    mock_download.assert_called_once()


def test_display_checks_task_status(mocker, stage_instance):
    mocker.patch("picli.config.Minio.list_objects", return_value=[mock.MagicMock()])
    mocker.patch("picli.stage.os.path.basename", return_value="blah")
    mocker.patch("builtins.open", new_callable=mock.mock_open)
    mocker.patch("picli.stage.util.download_artifact")
    mock_check = mocker.patch("picli.stage.Stage._check_task_status", return_value=True)
    stage_instance.stage_config.state = {
        "default": {"task_id": "blah"},
        "dependent": {"task_id": "blah"},
    }
    stage_instance.display()
    mock_check.assert_called_once()


def test_display_checks_task_status_failed(mocker, stage_instance):
    mocker.patch("picli.stage.Stage._check_task_status", return_value=False)
    stage_instance.stage_config.state = {
        "default": {"task_id": "blah"},
        "dependent": {"task_id": "blah"},
    }
    with pytest.raises(SystemExit):
        stage_instance.display()


def test_display_warns_no_artifacts(mocker, stage_instance):
    mocker.patch("picli.config.Minio.list_objects", return_value=[])
    mocker.patch("picli.stage.os.path.basename", return_value="blah")
    mocker.patch("picli.stage.Stage._check_task_status", return_value=True)
    stage_instance.stage_config.state = {
        "default": {"task_id": "blah"},
        "dependent": {"task_id": "blah"},
    }
    mock_log_warn = mocker.patch("picli.stage.LOG.warn")
    stage_instance.display()
    mock_log_warn.assert_called_once()


def test_zip_file_creates_file(stage_instance, tmpdir):
    temp_directory = tmpdir.mkdir("sub")
    temp_file = temp_directory.join("hello.txt")
    temp_file.write("content")
    stage_instance.stage_config.base_path = str(temp_directory)
    print(stage_instance.stage_config.base_path)
    zip_file = stage_instance._zip_files(str(tmpdir))
    assert isinstance(zip_file, zipfile.ZipFile)


def test_zip_file_ignores_state_directory(stage_instance, tmpdir):
    project_directory = tmpdir.mkdir(stage_instance.stage_config.project_name)
    state_directory = (
        project_directory.mkdir("piedpiper.d").mkdir("default").mkdir("state")
    )
    state_file = state_directory.join("state.yml")
    state_file.write("this_should_not_be_in_zip")
    stage_instance.stage_config.base_path = str(project_directory)
    zip_file = stage_instance._zip_files(str(tmpdir))

    assert not len(zip_file.namelist())


def test_upload_project_artifacts_calls_upload_artifacts(mocker, stage_instance):
    mocker.patch("picli.stage.util.generate_hashsum")
    mocker.patch("picli.stage.Stage._zip_files", return_value=mock.Mock())
    mock_upload = mocker.patch(
        "picli.stage.util.upload_artifacts", return_value=["uploaded"]
    )
    stage_instance._upload_project_artifacts()
    mock_upload.assert_called_once()


def test_execute_skips_stage_if_complete(stage_instance):
    stage_instance.stage_config.state = {"default": {"state": "completed"}}
    assert stage_instance.execute() is None


@pytest.mark.usefixtures("default_stage_execute_patches")
def test_execute_requests_task_id(mocker, stage_instance):
    mock_request_task = mocker.patch("picli.stage.util.request_new_task_id")
    stage_instance.execute()
    mock_request_task.assert_called_once()


@pytest.mark.usefixtures("default_stage_execute_patches")
def test_execute_checks_dependent_stages(mocker, stage_instance):
    check_dep = mocker.patch(
        "picli.stage.Stage._is_dependent_stage_state_completed", return_value=True
    )
    stage_instance.execute()
    check_dep.assert_called_once()


@pytest.mark.usefixtures("default_stage_execute_patches")
def test_execute_fails_dependent_stages(mocker, stage_instance):
    mocker.patch(
        "picli.stage.Stage._is_dependent_stage_state_completed", return_value=False
    )
    with pytest.raises(SystemExit):
        stage_instance.execute()


@pytest.mark.usefixtures("default_stage_execute_patches")
def test_execute_updates_state(mocker, stage_instance):
    mock_update_state = mocker.patch("picli.config.BaseConfig.update_state")
    stage_instance.execute()
    mock_update_state.assert_called_once_with({"default": {"state": "started"}})


@pytest.mark.usefixtures("default_stage_execute_patches")
def test_execute_calls_submit_job_with_resource_url(mocker, stage_instance):
    mocker.patch(
        "picli.stage.Stage._upload_project_artifacts", return_value="artifacts"
    )
    mocker.patch("picli.stage.util.request_new_task_id", return_value="1234")

    expected_resource_configs = [{"files": "*", "resource": "default"}]

    mock_submit_job = mocker.patch("picli.stage.Stage._submit_job")
    stage_instance.execute()
    mock_submit_job.assert_called_once_with(
        "http://172.17.0.1:8000/default",
        "artifacts",
        "1234",
        config=expected_resource_configs,
    )


@pytest.mark.usefixtures("default_stage_execute_patches")
def test_execute_invalid_resource_config(stage_instance):
    stage_instance.resources = {}
    with pytest.raises(SystemExit):
        stage_instance.execute()


@pytest.mark.usefixtures("default_stage_execute_patches")
def test_execute_wait_calls_display(mocker, stage_instance):
    mock_display = mocker.patch("picli.config.BaseConfig.display")
    stage_instance.execute(wait=True)
    mock_display.assert_called_once()


@pytest.mark.usefixtures("default_stage_execute_patches")
def test_execute_with_debug(mocker, stage_instance):
    mock_log_info = mocker.patch("picli.stage.LOG.debug")
    stage_instance.stage_config.debug = True
    stage_instance.execute()
    mock_log_info.assert_called()
