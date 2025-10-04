import click


@click.group()
def cli():
    pass


@cli.command()
@click.argument("request")
@click.option("--cmd", "-c", help="Command to get help for", required=False)
def help(request: str, cmd: str | None):
    if cmd:
        click.echo(f"Help for command '{cmd}':")
    click.echo(request)


cli.add_command(help)
