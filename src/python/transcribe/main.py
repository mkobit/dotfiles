import click
import os
import sys
import logging
from src.python.transcribe.transcriber import Transcriber
from src.python.transcribe.formatter import Formatter
from tqdm import tqdm

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Enums/Constants
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
@click.option(
    "--template-file", type=click.Path(exists=True), help="Jinja2 template file path."
)
@click.option("--template", help="Jinja2 template string.")
@click.option(
    "--output-dest",
    default="-",
    help="Output destination (file path or '-' for stdout). Default: stdout.",
)
def main(
    input_path: str,
    model: str,
    device: str,
    compute_type: str,
    language: str | None,
    template_file: str | None,
    template: str | None,
    output_dest: str,
) -> None:
    """
    Transcribe audio files using faster-whisper and Jinja2 templates.
    """

    # Validation
    if template_file and template:
        raise click.UsageError("Cannot provide both --template-file and --template.")

    try:
        logger.info(f"Loading model '{model}' on '{device}'...")
        transcriber = Transcriber(
            model_size=model, device=device, compute_type=compute_type
        )

        logger.info(f"Transcribing '{input_path}'...")
        segments_gen, info = transcriber.transcribe(input_path, language=language)

        logger.info(
            f"Detected language '{info.language}' with probability {info.language_probability:.2f}"
        )

        segments = []
        # Wrap generator with tqdm
        with tqdm(total=info.duration, unit="s", desc="Transcribing") as pbar:
            for segment in segments_gen:
                segments.append(segment)
                # Update progress bar based on segment end time
                current = pbar.n
                if segment.end > current:
                    pbar.update(segment.end - current)

        logger.info("Formatting output...")
        # Use the static method from Formatter class
        result = Formatter.format_segments(segments, info, template_file, template)

        if output_dest == "-":
            click.echo(result)
        else:
            with open(output_dest, "w") as f:
                f.write(result)
            logger.info(f"Output written to {output_dest}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
