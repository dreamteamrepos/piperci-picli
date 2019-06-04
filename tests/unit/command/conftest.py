import os
import pytest
import yaml


@pytest.helpers.register
def piedpiper_directories():
    pi_dirs = {
        "piedpiper.d/": {
            "default": {
                "file_vars.d/": None,
                "group_vars.d": None,
                "pipe_vars.d/": None,
            }
        }
    }
    return pi_dirs


@pytest.helpers.register
def piedpiper_config_fixture():
    config = {
        "project_name": "python_project",
        "version": "0.0.0",
        "gman_url": "http://172.17.0.1:8089/gman",
        "faas_endpoint": "http://172.17.0.1:8080",
        "storage": {
            "url": "172.17.0.1:9000",
            "access_key": "key1",
            "secret_key": "key2",
        },
    }
    return config


@pytest.helpers.register
def piedpiper_stages_fixture():
    stages = {
        "stages": [
            {
                "name": "default",
                "deps": [],
                "resources": [{"name": "default", "uri": "/default"}],
                "config": [{"files": "*", "resource": "default"}],
            },
            {
                "name": "dependent",
                "deps": ["default"],
                "resources": [{"name": "dependent", "uri": "/dependent"}],
                "config": [{"files": "*", "resource": "dependent"}],
            },
        ]
    }

    return stages


@pytest.helpers.register
def write_piedpiper_files(
    piedpiper_directories, piedpiper_config_fixture, piedpiper_stages_fixture
):
    def create_directories(d, current_dir="./"):
        for key, value in d.items():
            os.makedirs(os.path.join(current_dir, key), exist_ok=True)
            if type(value) == dict:
                create_directories(value, os.path.join(current_dir, key))

    create_directories(piedpiper_directories)
    with open(f"piedpiper.d/default/config.yml", "w") as f:
        f.write(yaml.dump(piedpiper_config_fixture()))
    with open(f"piedpiper.d/default/stages.yml", "w") as f:
        f.write(yaml.dump(piedpiper_stages_fixture()))
