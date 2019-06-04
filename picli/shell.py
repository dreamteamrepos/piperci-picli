import click

from picli import command


@click.group()
@click.option(
    "--config",
    "-c",
    default="piedpiper.d/default",
    help="The PiCli configuration file to use",
)
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging")
@click.pass_context
def main(context, config, debug):
    context.obj = {}
    context.obj["args"] = {}
    context.obj["args"]["config"] = config
    context.obj["args"]["debug"] = debug


main.add_command(command.run.run)
main.add_command(command.display.display)
