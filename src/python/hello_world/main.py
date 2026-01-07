#!/usr/bin/env python3
"""Hello World CLI - Example Python tool demonstrating build/deploy workflow.

This tool demonstrates:
- Multi-file Python application structure
- Click CLI framework for command-line interface
- Pydantic models for data validation
- Bazel-based build and testing
- Deployment via chezmoi hooks
"""

import click

from src.python.hello_world.lib import Logger, generate_greetings, write_output
from src.python.hello_world.models import AppConfig, Greeting, LogLevel


@click.command()
@click.argument("name")
@click.option(
    "-m",
    "--message",
    default="Hello",
    help="Greeting message to use",
)
@click.option(
    "-t",
    "--times",
    default=1,
    type=click.IntRange(1, 100),
    help="Number of times to repeat greeting",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default=None,
    help="Output file (default: stdout)",
)
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error"], case_sensitive=False),
    default="info",
    help="Logging level",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output (sets log level to debug)",
)
@click.version_option(version="1.0.0", prog_name="hello_world")
def main(
    name: str,
    message: str,
    times: int,
    output: str | None,
    log_level: str,
    verbose: bool,
) -> None:
    """Greet NAME with a customizable message.

    A simple demonstration CLI tool that shows how to build and deploy
    Python applications using Bazel and chezmoi.

    Examples:

        hello_world World

        hello_world --message "Hi" --times 3 Alice

        hello_world -v -o greetings.txt Bob
    """
    # Build configuration using pydantic models
    effective_log_level = LogLevel.DEBUG if verbose else LogLevel(log_level)
    config = AppConfig(
        log_level=effective_log_level,
        output_file=output,
        verbose=verbose,
    )

    # Initialize logger
    logger = Logger(config)
    logger.debug("Starting hello_world CLI")
    logger.debug(f"Configuration: {config.model_dump()}")

    # Create greeting model with validation
    try:
        greeting = Greeting(name=name, message=message, times=times)
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        raise click.ClickException(str(e)) from e

    # Generate and output greetings
    greetings = generate_greetings(greeting, logger)
    write_output(greetings, config, logger)

    logger.debug("Completed successfully")


if __name__ == "__main__":
    main()
