import typer

from termbud.scrollback import app as scrollback_app
from termbud.tmux import app as tmux_app
from termbud.zellij import app as zellij_app

app = typer.Typer(help="Terminal caddy tool")

app.add_typer(tmux_app, name="tmux")
app.add_typer(zellij_app, name="zellij")
app.add_typer(scrollback_app, name="scrollback")

if __name__ == "__main__":
    app()
