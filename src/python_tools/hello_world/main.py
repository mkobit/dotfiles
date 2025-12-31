import click
from src.python_tools.hello_world.lib import Greeting

@click.command()
@click.option('--name', default='World', help='Who to greet.')
def hello(name):
    """Simple program that greets NAME."""
    greeting = Greeting(message="Hello", name=name)
    click.echo(greeting.format())

if __name__ == '__main__':
    hello()
