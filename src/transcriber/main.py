#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from dataclasses import replace, asdict

import click
import whenever

import whisper

from src.transcriber.schemas import (
    ModelSize,
    Device,
    ModelInfo,
    FileInfo,
    TranscriptionMetadata,
    ModelDimensions,
)
from src.transcriber.render import render_template

BEAM_SIZE = 5


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--model-size",
    type=click.Choice([e.value for e in ModelSize]),
    default=ModelSize.BASE_EN.value,
    help="Model size",
)
@click.option(
    "--device",
    type=click.Choice([e.value for e in Device]),
    default=Device.AUTO.value,
    help="Device to use",
)
@click.option(
    "--template",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to custom Jinja2 template",
)
@click.option(
    "--output",
    "-o",
    type=click.File("w", encoding="utf-8"),
    default="-",
    help="Output file (default: stdout)",
)
@click.option("--verbose", is_flag=True, help="Print progress to stderr")
def main(
    input_file: Path,
    model_size: str,
    device: str,
    template: Path | None,
    output: click.utils.LazyFile,
    verbose: bool,
) -> None:
    """Transcribe audio files using openai-whisper."""

    start_time = time.monotonic()

    model_load_start = time.monotonic()
    click.echo(f"Loading model {model_size} on {device}...", err=True)

    model = whisper.load_model(model_size, device=device)

    model_load_end = time.monotonic()
    load_time = model_load_end - model_load_start
    click.echo(f"Model loaded in {load_time:.2f}s", err=True)

    file_stat = input_file.stat()
    file_info = FileInfo(
        path=str(input_file.absolute()),
        size_bytes=file_stat.st_size,
        duration_seconds=None,  # Will be updated after transcription start
    )

    transcription_start = time.monotonic()
    click.echo(f"Transcribing {input_file}...", err=True)

    # Capture timestamp before transcription starts
    timestamp = whenever.Instant.now()

    # OpenAI Whisper transcribe returns a dict
    # We use verbose=verbose to optionally show progress (segments)
    result = model.transcribe(str(input_file), beam_size=BEAM_SIZE, verbose=verbose)

    transcription_end = time.monotonic()
    transcription_time = transcription_end - transcription_start

    full_text = result["text"].strip()

    segments = result.get("segments", [])
    duration = segments[-1]["end"] if segments else 0.0

    file_info = replace(file_info, duration_seconds=duration)

    # model.dims is a NamedTuple or dataclass, convert to our schema
    dims = ModelDimensions(
        n_mels=model.dims.n_mels,
        n_audio_ctx=model.dims.n_audio_ctx,
        n_audio_state=model.dims.n_audio_state,
        n_audio_head=model.dims.n_audio_head,
        n_audio_layer=model.dims.n_audio_layer,
        n_vocab=model.dims.n_vocab,
        n_text_ctx=model.dims.n_text_ctx,
        n_text_state=model.dims.n_text_state,
        n_text_head=model.dims.n_text_head,
        n_text_layer=model.dims.n_text_layer,
    )

    metadata = TranscriptionMetadata(
        model=ModelInfo(
            size=ModelSize(model_size),
            device=Device(device),
            load_time_seconds=load_time,
            dims=dims,
            is_multilingual=model.is_multilingual,
        ),
        file=file_info,
        transcription_time_seconds=transcription_time,
        timestamp=timestamp,
        whisper_version=whisper.__version__,
    )

    rendered_output = render_template(
        template, {"metadata": metadata, "text": full_text}
    )

    output.write(rendered_output)
    if output != sys.stdout:
        click.echo(f"Output written to {output.name}", err=True)


if __name__ == "__main__":
    main()
