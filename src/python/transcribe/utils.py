def format_timestamp(seconds: float, vtt: bool = False) -> str:
    """
    Format seconds into SRT/VTT timestamp format.

    Args:
        seconds: Time in seconds.
        vtt: If True, use '.' separator (VTT), else ',' (SRT).

    Returns:
        Formatted timestamp string (HH:MM:SS,mmm or HH:MM:SS.mmm).
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)

    sep = "." if vtt else ","
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{sep}{millis:03d}"
