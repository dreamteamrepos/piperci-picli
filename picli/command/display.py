import click
from picli.config import BaseConfig
from picli import logger

LOG = logger.get_logger(__name__)


@click.command()
@click.option("--stages", help="Comma separated list of stages to display")
@click.option("--run-id", help="RunID of the jobs you want to display")
@click.pass_context
def display(context, stages, run_id):
    debug = context.obj.get("args")["debug"]
    config_directory = context.obj.get("args")["config"]
    config = BaseConfig(config_directory, clean_state=False, debug=debug)
    if stages:
        stages_list = stages.split(",")
        # Ensure given stages are valid
        config.get_sequence(stages=stages_list)
        sequence = stages_list
    else:
        stages_list = [s.name for s in config.stages]
        sequence = config.get_sequence(stages=stages_list)
    if not run_id:
        run_id = config.run_id

    config.display(sequence, run_id)
