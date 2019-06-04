import click
from picli.config import BaseConfig
from picli import logger

LOG = logger.get_logger(__name__)


@click.command()
@click.option("--stages", help="Comma separated list of stages to run")
@click.option(
    "--clean", is_flag=True, default=False, help="Run PiCli with a clean state file."
)
@click.option(
    "--wait",
    is_flag=True,
    default=False,
    help="Wait for PiCli remote job execution to finish and display results",
)
@click.pass_context
def run(context, stages, clean, wait):
    debug = context.obj.get("args")["debug"]
    config_directory = context.obj.get("args")["config"]
    config = BaseConfig(config_directory, clean_state=clean, debug=debug, wait=wait)
    if stages:
        stages_list = stages.split(",")
        sequence = config.get_sequence(stages=stages_list)
    else:
        stages_list = [s.name for s in config.stages]
        sequence = config.get_sequence(stages=stages_list)

    config.execute(sequence)
