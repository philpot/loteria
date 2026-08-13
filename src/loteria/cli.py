"""Console script for loteria."""

import typer
from rich.console import Console
# from loteria import utils
from loteria.gen import main as entry

app = typer.Typer(help="loteria")
console = Console()


@app.command()
def main(name:str = "world"):
    """Console script for loteria."""
    console.print(f"Hello {name}")
    console.print("Replace this message by putting your code into "
               "loteria.cli.main")
    console.print("See Typer documentation at https://typer.tiangolo.com/")
    # utils.do_something_useful()
    entry()


if __name__ == "__main__":
    app()
