#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from dataclasses import replace

import click
import whenever

import whisper

from src.transcriber.schemas import ModelSize, Device, ModelInfo, FileInfo, TranscriptionMetadata
from src.transcriber.render import render_template

BEAM_SIZE = 5

@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("--model-size", type=click.Choice([e.value for e in ModelSize]), default=ModelSize.BASE_EN.value, help="Model size")
@click.option("--device", type=click.Choice([e.value for e in Device]), default=Device.AUTO.value, help="Device to use")
@click.option("--template", type=click.Path(exists=True, path_type=Path), default=None, help="Path to custom Jinja2 template")
@click.option("--output", "-o", type=click.File("w", encoding="utf-8"), default="-", help="Output file (default: stdout)")
def main(
    input_file: Path,
    model_size: str,
    device: str,
    template: Path | None,
    output: click.utils.LazyFile,
) -> None:
    """Transcribe audio files using openai-whisper."""

    start_time = time.monotonic()

    # Load Model
    model_load_start = time.monotonic()
    click.echo(f"Loading model {model_size} on {device}...", err=True)

    model = whisper.load_model(model_size, device=device)

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

    # OpenAI Whisper transcribe returns a dict
    result = model.transcribe(str(input_file), beam_size=BEAM_SIZE, verbose=False)

    transcription_end = time.monotonic()
    transcription_time = transcription_end - transcription_start

    # Collect Text
    full_text = result["text"].strip()

    # OpenAI Whisper doesn't give info.duration easily in the return without inspecting audio first?
    # Actually it's not in the result dict usually. We might need to rely on ffmpeg or just skip duration if unknown.
    # But wait, result['segments'] might have timing.
    segments = result.get("segments", [])
    duration = segments[-1]["end"] if segments else 0.0

    # Update duration
    file_info = replace(file_info, duration_seconds=duration)

    # Prepare Metadata
    metadata = TranscriptionMetadata(
        model=ModelInfo(
            size=ModelSize(model_size),
            device=Device(device),
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
