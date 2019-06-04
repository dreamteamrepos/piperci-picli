from picli.model import stage_schema
from picli import logger
from picli import util

import logging
import os
import json
import requests
import tempfile
import zipfile

LOG = logger.get_logger(__name__)


class Stage:
    def __init__(self, stage_def, base_config):
        self.name = stage_def.get("name")
        self.stage_config = base_config
        self.dependencies = []
        self.resources = stage_def.get("resources")
        self.config = stage_def.get("config")
        self._validate(stage_def)
        if self.stage_config.debug:
            LOG.setLevel(logging.DEBUG)

    def _validate(self, stage_def):
        """
        Validate the loaded configuration object.
        Validations are defined in model/base_schema.py
        :return: None. Exit if errors are found.
        """
        errors = stage_schema.validate(stage_def)
        if errors:
            msg = f"Failed to validate. \n\n{errors.messages}"
            util.sysexit_with_message(msg)
        pass

    def add_dependency(self, stage):
        """
        Add a stage object as a dependency to this stage.
        :param stage: Stage object
        :return:
        """
        self.dependencies.append(stage)

    def _is_dependent_stage_state_completed(self):
        stages_not_complete = [
            stage
            for stage in self.dependencies
            if self.stage_config.state.get(stage.name)
            and self.stage_config.state.get(stage.name).get("state") != "completed"
        ]

        errors = []
        for stage in stages_not_complete:
            LOG.info(f"Checking if stage {stage.name} has completed")
            task_id_from_state = self.stage_config.state.get(stage.name).get("task_id")
            if not self._check_task_status(
                task_id_from_state, status="completed", stage=stage.name
            ):
                errors.append(stage.name)

        if len(errors):
            return False
        else:
            return True

    def _zip_files(self, destination):
        """
        Zips all files in the project and returns the zipfile
        object.
        :param destination: Path to create the zipfile in
        :return: ZipFile
        """
        zip_file = zipfile.ZipFile(
            f"{destination}/{self.stage_config.project_name}.zip",
            "w",
            zipfile.ZIP_DEFLATED,
        )
        for root, dirs, files in os.walk(self.stage_config.base_path):
            for file in files:

                state_path = os.path.realpath(
                    os.path.join(
                        self.stage_config.base_path, "piedpiper.d/default/state"
                    )
                )
                if os.path.commonpath(
                    [os.path.abspath(state_path)]
                ) == os.path.commonpath(
                    [
                        os.path.abspath(state_path),
                        os.path.abspath(os.path.join(root, file)),
                    ]
                ):
                    continue
                else:
                    zip_file.write(
                        os.path.join(root, file),
                        os.path.relpath(
                            os.path.join(root, file), self.stage_config.base_path
                        ),
                    )

        zip_file.close()

        return zip_file

    def _upload_project_artifacts(self):
        """
        Creates a zipfile of the project and uploads to the configured storage url
        :return: List of artifact dicts returned by util.upload_artifacts
        """
        with tempfile.TemporaryDirectory() as tempdir:
            artifact_file = self._zip_files(tempdir).filename
            artifact = {
                "file": artifact_file,
                "hashsum": util.generate_hashsum(artifact_file),
            }
            artifacts = util.upload_artifacts(
                run_id=self.stage_config.run_id,
                artifacts=[artifact],
                gman_url=self.stage_config.gman_url,
                storage_url=self.stage_config.storage.get("url"),
                access_key=self.stage_config.storage.get("access_key"),
                secret_key=self.stage_config.storage.get("secret_key"),
            )
        for artifact_state in artifacts:
            self.stage_config.update_state({self.name: {"artifacts": artifact_state}})

        return artifacts

    def _check_task_status(self, task_id, status="complete", stage=None):
        """
        Waits for task_id to be "status". Defaults to completed
        :param task_id: task_id string
        :param status: status string
        :return:
        """
        if stage is None:
            stage = self.name

        if util.wait_for_task_status(
            task_id=task_id,
            status=status,
            gman_url=self.stage_config.gman_url,
            retry_max=20,
        ):
            self.stage_config.update_state({stage: {"state": status}})
            return True

        else:
            self.stage_config.update_state({self.name: {"state": "failed"}})
            task_id_message = util.get_task_id_message(
                task_id, gman_url=self.stage_config.gman_url
            )
            message = (
                f"Remote job for stage {self.name} did not complete successfully."
                f"\n\n{util.safe_dump(task_id_message)}"
            )
            util.sysexit_with_message(message)

    def _submit_job(self, resource_url, artifacts, task_id, config=None):
        """
        Sends a Piedpiper job to a remote endpoint
        :param resource_url: The URL of the endpoint
        :param artifacts: List of artifact dicts
        :param task_id: task_id
        :return: JSON response from the endpoint
        """
        headers = {"Content-Type": "application/json"}

        task_data = {
            "run_id": self.stage_config.run_id,
            "project": self.stage_config.project_name,
            "artifacts": artifacts,
            "task_id": task_id,
            "configs": config,
            "stage": self.name,
        }
        try:
            r = requests.post(resource_url, data=json.dumps(task_data), headers=headers)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            message = f"Failed to call {resource_url} gateway. \n\n{e}"
            self.stage_config.update_state({self.name: {"state": "failed"}})
            util.update_task_id_status(
                self.stage_config.gman_url,
                task_id=task_id,
                status="failed",
                message=f"{message}",
            )
            util.sysexit_with_message(message)

        util.update_task_id_status(
            gman_url=self.stage_config.gman_url,
            task_id=task_id,
            status="info",
            message="Client received acceptance of job from gateway.",
        )
        self.stage_config.update_state(
            {
                self.name: {
                    "state": "running",
                    "client_task_id": task_id,
                    "task_id": r.json().get("task_id"),
                }
            }
        )

        return r.json()

    def display(self, run_id=None):
        """
        Displays the output of the stage by downloading the log artifact into a
        temporary directory.
        :return: The output of the log artifact for the stage to stdout
        """
        if not run_id:
            run_id = self.stage_config.run_id
        LOG.debug(f"Checking if task has completed")
        task_id_from_state = self.stage_config.state.get(self.name).get("task_id")
        if self._check_task_status(task_id_from_state, status="completed"):
            LOG.debug(f"Task has completed!")
        else:
            message = f"Waiting for job completion timed out"
            util.sysexit_with_message(message)

        LOG.info(f"Downloading artifacts for runID: {run_id}")
        # Convert generator returned by minio to a list so we can check if
        # it's empty before iterating.
        log_artifacts = list(
            self.stage_config.storage_client.list_objects(
                run_id, f"artifacts/logs/{self.name}", recursive=True
            )
        )
        if not len(log_artifacts):
            LOG.warn(f"No log artifacts found for stage {self.name}")
        for log_artifact in log_artifacts:
            with tempfile.TemporaryDirectory() as tempdir:
                local_path = f"{tempdir}/{os.path.basename(log_artifact.object_name)}"
                util.download_artifact(
                    run_id,
                    log_artifact.object_name,
                    local_path,
                    self.stage_config.storage_client,
                )
                LOG.info(f"Display artifact {log_artifact.object_name}")
                with open(local_path) as f:
                    LOG.warn(f.read())

    def execute(self, wait=False):
        """
        Execute a stage.
        First we check if all of our dependent stages are complete remotely.
        Then we check if the stage we are running is already marked as complete
        in the local state file.
        Then, request a new taskID from GMan for client execution tracking.
        For every glob in the stage config we parse out which resource to invoke.
        Calls the requested resource and waits for the returned taskID to finish executing
        :return: None
        """
        if (
            self.stage_config.state.get(self.name)
            and self.stage_config.state.get(self.name).get("state") == "completed"
        ):
            LOG.info(
                f"Stage {self.name} marked complete in local state file. Skipping..."
            )
            return
        if not self._is_dependent_stage_state_completed():
            message = (
                f"Stage dependencies '{[dep.name for dep in self.dependencies]}' "
                f"are not complete. Check your state file"
            )
            util.sysexit_with_message(message)

        task_id = util.request_new_task_id(
            run_id=self.stage_config.run_id,
            gman_url=self.stage_config.gman_url,
            project=self.stage_config.project_name,
            caller="picli",
        )
        LOG.debug(f"Received taskID {task_id} from gman")

        self.stage_config.update_state({self.name: {"state": "started"}})

        artifacts = self._upload_project_artifacts()

        for unique_resource in {config.get("resource") for config in self.config}:
            resource_configs = [
                config
                for config in self.config
                if config.get("resource") == unique_resource
            ]
            try:
                resource_uri = next(
                    r.get("uri")
                    for r in self.resources
                    if unique_resource == r.get("name")
                )
                resource_url = self.stage_config.faas_endpoint + resource_uri
            except StopIteration:
                LOG.fatal(
                    f"Resource {unique_resource} not found in stages.yml"
                    f"for stage {self.name}.\n"
                    f"{util.safe_dump(self.resources)}"
                )
                util.sysexit_with_message("Failed")

            LOG.info(f"Sending to {resource_uri}")

            job_results = self._submit_job(
                resource_url, artifacts, task_id, config=resource_configs
            )
            self._check_task_status(job_results.get("task_id"), status="started")
            LOG.debug(
                f"Job submitted for stage {self.name} to {resource_url} "
                f"with task_id {job_results.get('task_id')}"
            )

            if wait:
                self._check_task_status(job_results.get("task_id"), status="completed")
                self.stage_config.display([self.name], self.stage_config.run_id)
