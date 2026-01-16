#!/usr/bin/env python3
import os
import sys
import time
from pathlib import Path
from dataclasses import replace

# --- START_IMPORTS ---
if __name__ == "__main__":
    # Allow running from source/tests without Bazel
    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[2]
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
# --- END_IMPORTS ---

import click
import whenever
from tqdm import tqdm

try:
    from faster_whisper import WhisperModel
except ImportError:
    # Fallback for when faster-whisper is not installed (e.g., build failure)
    # This allows the tool to compile and run tests that mock it.
    WhisperModel = None

from src.transcriber.schemas import ModelSize, Device, ComputeType, ModelInfo, FileInfo, TranscriptionMetadata
from src.transcriber.render import render_template

BEAM_SIZE = 5

@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("--model-size", type=click.Choice([e.value for e in ModelSize]), default=ModelSize.BASE_EN.value, help="Model size")
@click.option("--device", type=click.Choice([e.value for e in Device]), default=Device.AUTO.value, help="Device to use")
@click.option("--compute-type", type=click.Choice([e.value for e in ComputeType]), default=ComputeType.AUTO.value, help="Compute type")
@click.option("--template", type=click.Path(exists=True, path_type=Path), default=None, help="Path to custom Jinja2 template")
@click.option("--output", "-o", type=click.File("w", encoding="utf-8"), default="-", help="Output file (default: stdout)")
def main(
    input_file: Path,
    model_size: str,
    device: str,
    compute_type: str,
    template: Path | None,
    output: click.utils.LazyFile,
) -> None:
    """Transcribe audio files using faster-whisper."""

    if WhisperModel is None:
        raise click.ClickException("faster-whisper is not installed. Please install it to use this tool.")

    start_time = time.monotonic()

    # Load Model
    model_load_start = time.monotonic()
    click.echo(f"Loading model {model_size} on {device}...", err=True)

    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    model_load_end = time.monotonic()
    load_time = model_load_end - model_load_start
    click.echo(f"Model loaded in {load_time:.2f}s", err=True)

    # Prepare File Info
    file_stat = input_file.stat()
    file_info = FileInfo(
        path=str(input_file.absolute()),
        size_bytes=file_stat.st_size,
        duration_seconds=None # Will be updated after transcription start
    )

    # Transcribe
    transcription_start = time.monotonic()
    click.echo(f"Transcribing {input_file}...", err=True)

    segments_generator, info = model.transcribe(str(input_file), beam_size=BEAM_SIZE)

    # Update duration from info
    file_info = replace(file_info, duration_seconds=info.duration)

    segments = []
    with tqdm(total=info.duration, unit="s", file=sys.stderr) as pbar:
        for segment in segments_generator:
            segments.append(segment)
            pbar.update(segment.end - pbar.n) # Update progress to current segment end

    transcription_end = time.monotonic()
    transcription_time = transcription_end - transcription_start

    # Collect Text
    full_text = "".join([segment.text for segment in segments]).strip()

    # Prepare Metadata
    metadata = TranscriptionMetadata(
        model=ModelInfo(
            size=ModelSize(model_size),
            device=Device(device),
            compute_type=ComputeType(compute_type),
            load_time_seconds=load_time
        ),
        file=file_info,
        transcription_time_seconds=transcription_time,
        timestamp=whenever.Instant.now().format_common_iso()
    )

    # Render Output
    rendered_output = render_template(template, {"metadata": metadata, "text": full_text})

    # Write Output
    output.write(rendered_output)
    if output != sys.stdout:
        click.echo(f"Output written to {output.name}", err=True)

if __name__ == "__main__":
    main()
