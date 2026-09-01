import sys


def main() -> None:
    command = sys.argv[1:3]
    if command == ["antigravity", "render"]:
        from termstatus.agy import render_from_stdin  # noqa: PLC0415

        render_from_stdin()
        return
    from termstatus.main import main as typer_main  # noqa: PLC0415

    typer_main()
