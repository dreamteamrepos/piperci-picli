import click
from click.testing import CliRunner
import mock
import os
import pytest
import yaml

from picli.shell import main
from picli.config import BaseConfig


@pytest.mark.parametrize(
    "input_stages, expected_stages",
    [
        ("default,dependent", ["default", "dependent"]),
        ("dependent,default", ["dependent", "default"]),
        ("", ["default", "dependent"]),
    ],
)
def test_display_displays_given_sequence(input_stages, expected_stages):
    with mock.patch.object(BaseConfig, "display", spec=BaseConfig) as mock_display:
        runner = CliRunner()
        with runner.isolated_filesystem():
            pytest.helpers.write_piedpiper_files(
                pytest.helpers.piedpiper_directories(),
                pytest.helpers.piedpiper_config_fixture,
                pytest.helpers.piedpiper_stages_fixture,
            )
            command = (
                ["display", "--stages", input_stages]
                if len(input_stages)
                else ["display"]
            )
            runner.invoke(main, command, catch_exceptions=False)
            args, kwargs = mock_display.call_args
            assert expected_stages in args


@pytest.mark.parametrize("input_stages, expected_failure", [("no_stage", 1)])
def test_display_fails_invalid_sequence(input_stages, expected_failure):
    with mock.patch.object(BaseConfig, "display", spec=BaseConfig):
        runner = CliRunner()
        with runner.isolated_filesystem():
            pytest.helpers.write_piedpiper_files(
                pytest.helpers.piedpiper_directories(),
                pytest.helpers.piedpiper_config_fixture,
                pytest.helpers.piedpiper_stages_fixture,
            )
            command = (
                ["display", "--stages", input_stages]
                if len(input_stages)
                else ["display"]
            )
            results = runner.invoke(main, command)
            assert results.exit_code == expected_failure
