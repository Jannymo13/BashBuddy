import click
import os
from google import genai
from dotenv import load_dotenv


@click.command()
@click.argument("request")
@click.option("--cmd", "-c", help="Command to get help for", required=False)
def ask(request: str, cmd: str | None):
    load_dotenv() 
    if cmd:
        click.echo(f"Help for command '{cmd}':")
    click.echo(request)
    click.echo(os.getcwd())

    # client = genai.Client( api_key=os.getenv("GENAI_API_KEY"))
    # response = client.models.generate_content(
    #         model="gemini-2.5-flash",
    #         contents="Explain how AI works in a few words",
    #         )
    click.echo(os.getenv("GEMINI_API_KEY"))


