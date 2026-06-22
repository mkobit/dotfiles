import typer

from agent_sandbox.profile.loader import load_config
from agent_sandbox.profile.schema import ConfigError

app = typer.Typer()


@app.command()
def profiles() -> None:
    """List available sandbox profiles and their capability settings."""
    try:
        config = load_config()
    except ConfigError as exc:
        typer.secho(f"agent-run: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    for name, profile in sorted(config.profiles.items()):
        marker = " (default)" if name == config.default_profile else ""
        typer.echo(f"{name}{marker}")
        typer.echo(f"  backend={profile.backend}  network={profile.network}")
        typer.echo(f"  project_write={profile.project_write}")
        typer.echo(f"  ssh_agent={profile.ssh_agent}  gpg_agent={profile.gpg_agent}")
        if profile.extra_ro:
            typer.echo(f"  extra_ro={list(profile.extra_ro)}")
        if profile.extra_rw:
            typer.echo(f"  extra_rw={list(profile.extra_rw)}")
        typer.echo("")
