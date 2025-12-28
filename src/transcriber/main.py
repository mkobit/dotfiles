# /// script
# dependencies = [
#   "click",
#   "faster-whisper",
#   "jinja2",
#   "tqdm",
# ]
# ///

import os
import time
import click
import hashlib
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import sys

# --- START_IMPORTS ---
# Add current directory to sys.path to ensure local modules can be imported
# even when running as a script or within Bazel structure.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from schemas import ModelInfo, FileInfo, TranscriptionMetadata, TranscriptionResult
    from render import render_template
except ImportError as e1:
    try:
        from src.transcriber.schemas import ModelInfo, FileInfo, TranscriptionMetadata, TranscriptionResult
        from src.transcriber.render import render_template
    except ImportError as e2:
        # Check if classes are already defined (e.g. by inlining/concatenation)
        if 'FileInfo' in globals():
            pass
        else:
            raise ImportError(f"Imports failed. CWD: {os.getcwd()}. sys.path: {sys.path}. E1: {e1}. E2: {e2}")
# --- END_IMPORTS ---

def get_file_info(file_path: str) -> 'FileInfo':
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
@click.option('--template', '-t', type=click.Path(exists=True), help='Path to Jinja2 template file.')
@click.option('--output', '-o', type=click.Path(), help='Output file path.')
@click.option('--model', '-m', default='base', help='Whisper model size (tiny, base, small, medium, large-v3).')
@click.option('--device', default='auto', help='Device to use (cuda, cpu, auto).')
@click.option('--compute-type', default='default', help='Compute type (float16, int8_float16, int8, etc).')
def transcribe(audio_file, template, output, model, device, compute_type):
    """
    Transcribe AUDIO_FILE using faster-whisper and render the result using a Jinja2 template.
    """
    start_time = time.time()

    # Lazy import to avoid heavy load if just asking for help
    from faster_whisper import WhisperModel

    click.echo(f"Loading model {model} on {device}...")

    # Initialize model
    whisper = WhisperModel(model, device=device, compute_type=compute_type)

    click.echo(f"Transcribing {audio_file}...")

    # Transcribe
    segments, info = whisper.transcribe(audio_file, beam_size=5)

    # Collect segments with progress bar
    transcribed_segments = []
    total_duration = info.duration

    with tqdm(total=total_duration, unit="s") as pbar:
        for segment in segments:
            transcribed_segments.append(segment)
            pbar.update(segment.end - segment.start)
            # pbar.update(segment.end - (pbar.n or 0)) # simpler logic needed for updates

    text = "\n".join([s.text for s in transcribed_segments])

    end_time = time.time()
    transcription_time = end_time - start_time

    # Metadata construction
    file_info = get_file_info(audio_file)
    # Update duration from info
    object.__setattr__(file_info, 'duration_seconds', info.duration)

    model_info = ModelInfo(
        name=model,
        size=model, # Simplified
        device=device,
        compute_type=compute_type
    )

    metadata = TranscriptionMetadata(
        transcription_time_seconds=transcription_time,
        model=model_info,
        file=file_info,
        cli_args={
            "date": datetime.now().isoformat(),
            "output_path": output
        },
        template_name=template if template else "default",
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
        output_content = render_template(template, result.to_dict())

    if output:
        with open(output, 'w') as f:
            f.write(output_content)
        click.echo(f"Transcription saved to {output}")
    else:
        click.echo(output_content)

if __name__ == '__main__':
    transcribe()
