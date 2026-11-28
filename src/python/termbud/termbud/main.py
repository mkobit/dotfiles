import typer

from termbud.zellij import app as zellij_app

app = typer.Typer(help="Terminal caddy tool")

app.add_typer(zellij_app, name="zellij")

if __name__ == "__main__":
    app()
