from minio import Minio
import shutil
import os

from picli.model import base_schema
from picli import logger
from picli.stage import Stage
from picli import util

LOG = logger.get_logger(__name__)


class BaseConfig(object):
    def __init__(self, config_dir, clean_state=True, debug=False, wait=False):
        self.debug = debug
        self.base_path = self._find_base_path(config_dir)
        self.config_dir = config_dir
        self.config = self._read_config()
        self._validate()
        self.gman_url = self.config["gman_url"]
        self.storage = self.config["storage"]
        self.faas_endpoint = self.config["faas_endpoint"]
        self.project_name = self.config["project_name"]
        self.version = self.config["version"]
        self.stages = self._build_stages(self.read_stage_defs())
        self._state_file = f"{self.state_directory}/state.yml"
        self.clean_state = clean_state
        self._create_state_file()
        self.state = {} if clean_state else self.read_state_file()
        if clean_state:
            self._clean_state()
        self.run_id = self._get_run_id()
        self.storage_client = self._init_storage_client()
        self.wait = wait

    def _get_run_id(self):
        if self.clean_state:
            run_id = self._generate_run_id()
        else:
            try:
                run_id = util.safe_load_file(self._state_file)["run_id"]
            except KeyError:
                LOG.warn(
                    "There was no run_id found in state file. Generating new state file"
                )
                self._clean_state()
                run_id = self._generate_run_id()

        return run_id

    def _generate_run_id(self):
        run_id = util.generate_run_id()
        run_id_state = {"run_id": run_id}
        self.update_state(run_id_state)
        return run_id

    def _init_storage_client(self):
        minio_client = Minio(
            self.storage["url"],
            access_key=self.storage["access_key"],
            secret_key=self.storage["secret_key"],
            secure=False,
        )
        return minio_client

    @property
    def state_directory(self):
        return f"{self.config_dir}/state"

    def _create_state_file(self):
        os.makedirs(self.state_directory, exist_ok=True)
        if not os.path.isfile(os.path.join(self.state_directory, "state.yml")):
            with open(self._state_file, "w") as f:
                f.write(util.safe_dump({}))

    def _clean_state(self):
        self.state = {}
        shutil.rmtree(self.state_directory, ignore_errors=True)
        self._create_state_file()

    def update_state(self, state):
        updated_state = util.merge_dicts(self.state, state)
        self.state = updated_state
        self.write_state_file()

    def write_state_file(self):
        with open(self._state_file, "w") as f:
            f.write(util.safe_dump(self.state))

    def read_state_file(self):
        return util.safe_load_file(self._state_file)

    def read_stage_defs(self):
        stage_definitions = util.safe_load_file(
            os.path.join(self.config_dir, "stages.yml")
        )["stages"]
        return stage_definitions

    def _build_stages(self, stage_definitions):
        stages = [Stage(stage, self) for stage in stage_definitions]
        for stage in stages:
            # sum([comprehension], []) will give us a flattened list
            for dep in sum(
                [
                    item.get("deps")
                    for item in stage_definitions
                    if item.get("name") == stage.name and item.get("deps")
                ],
                [],
            ):
                dependent_nodes = [node for node in stages if node.name == dep]
                for dependent_node in dependent_nodes:
                    stage.add_dependency(dependent_node)

        return stages

    def _find_base_path(self, config):
        """

        :param config: Piedpiper configuration directory
        :return: Directory that is two levels up from
        configuration file. This will be the base directory
        that all other methods will assume.
        """
        base_path = os.path.normpath(os.path.join(os.path.abspath(config), "../.."))
        return base_path

    def _read_config(self):
        """
        Read config.yml configuration file
        and return a dict.
        :return: attrdict
        """
        return util.safe_load_file(os.path.join(self.config_dir, "config.yml"))

    def _validate(self):
        """
        Validate the loaded configuration object.
        Validations are defined in model/base_schema.py
        :return: None. Exit if errors are found.
        """
        errors = base_schema.validate(self.config)
        if errors:
            msg = f"Failed to validate. \n\n{errors.messages}"
            util.sysexit_with_message(msg)

    @staticmethod
    def _dep_resolve(node, resolved, seen):
        seen.append(node)
        if node.dependencies:
            for stage in node.dependencies:
                if stage not in resolved:
                    if stage in seen:
                        util.sysexit_with_message(
                            f"Circular reference detected: {node.name} -> {stage.name}"
                        )
                    BaseConfig._dep_resolve(stage, resolved, seen)
        if node not in resolved:
            resolved.append(node)
        seen.remove(node)

    @property
    def piedpiper_dir(self):
        """
        Property defining the location of the pipedpiper.d directory.

        :return: String of path to piedpiper.d directory.
        """
        piedpiper_dir = os.path.join(self.base_path, "piedpiper.d")
        if os.path.isdir(f"{piedpiper_dir}"):
            return piedpiper_dir
        else:
            message = f"Piedpiper directory doesn't exist in {piedpiper_dir}."
            util.sysexit_with_message(message)

    def get_sequence(self, stages=[]):
        """
        Builds a list of actions to execute based on the
        stages.yml configuration. We will walk the dependency
        list in the configuration file for the list of stages we
        were passed to build up our action list.
        :param stage_definitions
        :param stages
        :return: A list of actions to run
        """
        for stage in stages:
            try:
                assert stage in [
                    stage_def["name"] for stage_def in self.read_stage_defs()
                ]
            except AssertionError:
                message = (
                    f"Invalid stage passed to PiCli."
                    f'Stage "{stage}" does not exist in stages.yml.'
                )
                util.sysexit_with_message(message)

        stages_to_run = []
        for stage in stages:
            stage_to_run = next(s for s in self.stages if s.name == stage)
            BaseConfig._dep_resolve(stage_to_run, stages_to_run, [])

        return [stage.name for stage in stages_to_run]

    def execute(self, stages):
        """
        Execute a list of stages
        :param stages: List
        :return: None
        """
        # Zip files in project directory
        # Get task ID
        # Generate hash
        # Upload artifact is hash doesn't match
        for stage in stages:
            LOG.info(f"Executing stage: {stage}")
            [s.execute(wait=self.wait) for s in self.stages if s.name == stage]

    def display(self, stages, run_id):
        """
        Displays the results of a list of stages
        :param stages: List of stages
        :return: None
        """
        for stage in stages:
            LOG.info(f"Displaying stage results: {stage}")
            [s.display(run_id) for s in self.stages if s.name == stage]
