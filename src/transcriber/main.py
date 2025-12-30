import os
import time
import click
import hashlib
import whenever
from pathlib import Path
from tqdm import tqdm
import sys
import dataclasses
from typing import Optional

# --- START_IMPORTS ---
# Add current directory to sys.path to ensure local modules can be imported
# even when running as a script or within Bazel structure.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# --- END_IMPORTS ---

from schemas import (
    ModelInfo,
    FileInfo,
    TranscriptionMetadata,
    TranscriptionResult,
    ModelSize,
    Device,
    ComputeType
)
from render import render_template

# Default beam size for transcription
BEAM_SIZE = 5

def get_file_info(file_path: str) -> FileInfo:
    path = Path(file_path)
    stat = path.stat()
    return FileInfo(
        path=str(path.absolute()),
        name=path.name,
        size_bytes=stat.st_size,
        duration_seconds=None # Populated later if possible
    )

@click.command()
@click.argument('audio_file', type=click.Path(exists=True))
@click.option('--template', '-t', type=click.Path(exists=True, path_type=Path), help='Path to Jinja2 template file.')
@click.option('--output', '-o', type=click.File('w'), default='-', help='Output file path (default: stdout).')
@click.option('--model', '-m', type=click.Choice([e.value for e in ModelSize]), default=ModelSize.BASE.value, help='Whisper model size.')
@click.option('--device', type=click.Choice([e.value for e in Device]), default=Device.AUTO.value, help='Device to use.')
@click.option('--compute-type', type=click.Choice([e.value for e in ComputeType]), default=ComputeType.DEFAULT.value, help='Compute type.')
def transcribe(audio_file, template, output, model, device, compute_type):
    """
    Transcribe AUDIO_FILE using faster-whisper and render the result using a Jinja2 template.
    """

    # Lazy import to avoid heavy load if just asking for help
    from faster_whisper import WhisperModel

    load_start = time.monotonic()
    click.echo(f"Loading model {model} on {device}...", err=True)

    # Initialize model
    whisper = WhisperModel(model, device=device, compute_type=compute_type)
    load_duration = time.monotonic() - load_start

    click.echo(f"Transcribing {audio_file}...", err=True)

    transcribe_start = time.monotonic()
    # Transcribe
    segments, info = whisper.transcribe(audio_file, beam_size=BEAM_SIZE)

    # Collect segments with progress bar
    transcribed_segments = []
    total_duration = info.duration

    with tqdm(total=total_duration, unit="s", file=sys.stderr) as pbar:
        for segment in segments:
            transcribed_segments.append(segment)
            pbar.update(segment.end - segment.start)

    text = "\n".join([s.text for s in transcribed_segments])

    transcription_time = time.monotonic() - transcribe_start

    # Metadata construction
    file_info = get_file_info(audio_file)
    # Update duration safely using replace
    file_info = dataclasses.replace(file_info, duration_seconds=info.duration)

    model_info = ModelInfo(
        name=model,
        size=model,
        device=device,
        compute_type=compute_type
    )

    metadata = TranscriptionMetadata(
        transcription_time_seconds=transcription_time,
        load_time_seconds=load_duration,
        model=model_info,
        file=file_info,
        cli_args={
            "date": whenever.Instant.now().format_common_iso(),
            "output_path": output.name if hasattr(output, 'name') else "stdout"
        },
        template_name=str(template) if template else "default",
        tool_version="0.1.0"
    )

    result = TranscriptionResult(
        text=text,
        segments=transcribed_segments,
        metadata=metadata
    )

    # Output handling
    output_content = text
    if template:
        # render_template expects Path
        output_content = render_template(template, result.to_dict())

    output.write(output_content)
    if output.name != '<stdout>':
        click.echo(f"Transcription saved to {output.name}", err=True)

if __name__ == '__main__':
    transcribe()
