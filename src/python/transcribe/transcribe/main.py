import logging
import sys
from pathlib import Path
from typing import Annotated

import typer
from tqdm import tqdm

from transcribe.formatter import Formatter
from transcribe.transcriber import FasterWhisperTranscriber

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

cli = typer.Typer(add_completion=False)


@cli.command()
def main(
    input_path: Annotated[Path, typer.Argument(exists=True, help="Path to input audio file")],
    model: Annotated[str, typer.Option(help="Model size. Default: base.")] = "base",
    device: Annotated[str, typer.Option(help="Device to use. Default: auto.")] = "auto",
    compute_type: Annotated[str, typer.Option(help="Compute type. Default: default.")] = "default",
    language: Annotated[str | None, typer.Option(help="Language code (optional).")] = None,
    template_file: Annotated[Path | None, typer.Option(exists=True, help="Jinja2 template file path.")] = None,
    template: Annotated[str | None, typer.Option(help="Jinja2 template string.")] = None,
    output_dest: Annotated[
        str, typer.Option(help="Output destination (file path or '-' for stdout). Default: stdout.")
    ] = "-",
) -> None:
    """Transcribe audio files using faster-whisper and Jinja2 templates."""
    if template_file and template:
        typer.echo("Error: Cannot provide both --template-file and --template.", err=True)
        raise typer.Exit(code=2)

    try:
        logger.info(f"Loading model '{model}' on '{device}'...")
        transcriber = FasterWhisperTranscriber(model_size=model, device=device, compute_type=compute_type)

        logger.info(f"Transcribing '{input_path}'...")
        segments_gen, info = transcriber.transcribe(str(input_path), language=language)

        logger.info(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")

        segments = []
        with tqdm(total=info.duration, unit="s", desc="Transcribing") as pbar:
            for segment in segments_gen:
                segments.append(segment)
                current = pbar.n
                if segment.end > current:
                    pbar.update(segment.end - current)

        logger.info("Formatting output...")
        template_file_str = str(template_file) if template_file else None
        result = Formatter.format_segments(segments, info, template_file_str, template)

        if output_dest == "-":
            typer.echo(result)
        else:
            with open(output_dest, "w") as f:
                f.write(result)
            logger.info(f"Output written to {output_dest}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
