import logging
import sys
from dataclasses import dataclass
from typing import Any

import click
from tqdm import tqdm

from transcribe.formatter import Formatter
from transcribe.transcriber import Transcriber

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

MODEL_SIZES = [
    "tiny",
    "tiny.en",
    "base",
    "base.en",
    "small",
    "small.en",
    "medium",
    "medium.en",
    "large-v1",
    "large-v2",
    "large-v3",
    "large",
]
DEVICES = ["cpu", "cuda", "auto"]
COMPUTE_TYPES = ["float16", "int8_float16", "int8", "default"]


@dataclass(frozen=True)
class TranscribeConfig:
    input_path: str
    model: str
    device: str
    compute_type: str
    output_dest: str
    language: str | None = None
    template_file: str | None = None
    template: str | None = None


@click.command()
@click.argument("input_path", type=click.Path(exists=True), required=True)
@click.option(
    "--model",
    type=click.Choice(MODEL_SIZES),
    default="base",
    help="Model size. Default: base.",
)
@click.option(
    "--device",
    type=click.Choice(DEVICES),
    default="auto",
    help="Device to use. Default: auto.",
)
@click.option(
    "--compute-type",
    type=click.Choice(COMPUTE_TYPES),
    default="default",
    help="Compute type. Default: default.",
)
@click.option("--language", default=None, help="Language code (optional).")
@click.option("--template-file", type=click.Path(exists=True), help="Jinja2 template file path.")
@click.option("--template", help="Jinja2 template string.")
@click.option(
    "--output-dest",
    default="-",
    help="Output destination (file path or '-' for stdout). Default: stdout.",
)
def main(**kwargs: Any) -> None:
    """
    Transcribe audio files using faster-whisper and Jinja2 templates.
    """
    config = TranscribeConfig(**kwargs)

    if config.template_file and config.template:
        raise click.UsageError("Cannot provide both --template-file and --template.")

    try:
        logger.info(f"Loading model '{config.model}' on '{config.device}'...")
        transcriber = Transcriber(model_size=config.model, device=config.device, compute_type=config.compute_type)

        logger.info(f"Transcribing '{config.input_path}'...")
        segments_gen, info = transcriber.transcribe(config.input_path, language=config.language)

        logger.info(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")

        segments = []
        with tqdm(total=info.duration, unit="s", desc="Transcribing") as pbar:
            for segment in segments_gen:
                segments.append(segment)
                current = pbar.n
                if segment.end > current:
                    pbar.update(segment.end - current)

        logger.info("Formatting output...")
        result = Formatter.format_segments(segments, info, config.template_file, config.template)

        if config.output_dest == "-":
            click.echo(result)
        else:
            with open(config.output_dest, "w") as f:
                f.write(result)
            logger.info(f"Output written to {config.output_dest}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
