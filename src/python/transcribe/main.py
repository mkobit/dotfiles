import click
import os
import sys
from src.python.transcribe.transcriber import Transcriber
from src.python.transcribe.formatter import Formatter
from typing import Optional
from tqdm import tqdm

@click.command()
@click.argument("input_path", type=click.Path(exists=True), required=True)
@click.option("--model", default="base", help="Model size (tiny, base, small, medium, large-v3). Default: base.")
@click.option("--device", default="auto", help="Device to use (cpu, cuda, auto). Default: auto.")
@click.option("--compute-type", default="default", help="Compute type (float16, int8_float16, int8, default). Default: default.")
@click.option("--language", default=None, help="Language code (optional).")
@click.option("--template-file", type=click.Path(exists=True), help="Jinja2 template file path.")
@click.option("--template-string", help="Jinja2 template string.")
@click.option("--output-dest", default="-", help="Output destination (file path or '-' for stdout). Default: stdout.")
def main(input_path: str, model: str, device: str, compute_type: str, language: Optional[str],
         template_file: Optional[str], template_string: Optional[str], output_dest: str) -> None:
    """
    Transcribe audio files using faster-whisper and Jinja2 templates.
    """

    # Validation
    if template_file and template_string:
         raise click.UsageError("Cannot provide both --template-file and --template-string.")

    try:
        click.echo(f"Loading model '{model}' on '{device}'...", err=True)
        transcriber = Transcriber(model_size=model, device=device, compute_type=compute_type)

        click.echo(f"Transcribing '{input_path}'...", err=True)
        segments_gen, info = transcriber.transcribe(input_path, language=language)

        click.echo(f"Detected language '{info.language}' with probability {info.language_probability:.2f}", err=True)

        segments = []
        # Wrap generator with tqdm
        with tqdm(total=info.duration, unit="s", desc="Transcribing") as pbar:
            for segment in segments_gen:
                segments.append(segment)
                # Update progress bar based on segment end time
                current = pbar.n
                if segment.end > current:
                    pbar.update(segment.end - current)

        click.echo("Formatting output...", err=True)
        # Use the static method from Formatter class
        result = Formatter.format_segments(segments, info, template_file, template_string)

        if output_dest == "-":
            click.echo(result)
        else:
            with open(output_dest, "w") as f:
                f.write(result)
            click.echo(f"Output written to {output_dest}", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
