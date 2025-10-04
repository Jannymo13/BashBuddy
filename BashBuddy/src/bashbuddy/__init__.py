import click
from bashbuddy.ask import ask

@click.group()
def cli():
    pass

cli.add_command(ask)
