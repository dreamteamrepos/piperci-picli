from click.testing import CliRunner
import mock
import pytest

from picli.shell import main
from picli.config import BaseConfig


@pytest.mark.parametrize(
    "input_stages, expected_stages",
    [
        ("dependent,default", ["default", "dependent"]),
        ("default,dependent", ["default", "dependent"]),
        ("", ["default", "dependent"]),
    ],
)
def test_run_executes_given_sequence(input_stages, expected_stages):
    with mock.patch.object(BaseConfig, "execute", spec=BaseConfig) as mock_execute:
        runner = CliRunner()
        with runner.isolated_filesystem():
            pytest.helpers.write_piedpiper_files(
                pytest.helpers.piedpiper_directories(),
                pytest.helpers.piedpiper_config_fixture,
                pytest.helpers.piedpiper_stages_fixture,
            )
            command = (
                ["run", "--stages", input_stages] if len(input_stages) else ["run"]
            )
            runner.invoke(main, command, catch_exceptions=False)
            mock_execute.assert_called_once_with(expected_stages)


@pytest.mark.parametrize("input_stages, expected_failure", [("no_stage", 1)])
def test_run_fails_invalid_sequence(input_stages, expected_failure):
    with mock.patch.object(BaseConfig, "execute", spec=BaseConfig):
        runner = CliRunner()
        with runner.isolated_filesystem():
            pytest.helpers.write_piedpiper_files(
                pytest.helpers.piedpiper_directories(),
                pytest.helpers.piedpiper_config_fixture,
                pytest.helpers.piedpiper_stages_fixture,
            )
            command = (
                ["run", "--stages", input_stages] if len(input_stages) else ["run"]
            )
            results = runner.invoke(main, command)
            assert results.exit_code == expected_failure
