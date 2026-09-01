import sys


def main() -> None:
    command = sys.argv[1:3]
    if command == ["antigravity", "render"]:
        from termstatus.agy import render_from_stdin

        render_from_stdin()
        return
    if command == ["antigravity", "title"]:
        from termstatus.agy import title_from_stdin

        title_from_stdin()
        return
    from termstatus.main import main as typer_main

    typer_main()
