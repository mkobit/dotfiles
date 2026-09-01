import asyncio
import json
import sys

from termstatus.agy.git import fallback_vcs, resolve_vcs
from termstatus.agy.protocol import decode_payload, mapping
from termstatus.agy.statusline import render_statusline


def render_from_stdin() -> None:
    try:
        payload = decode_payload(mapping(json.loads(sys.stdin.read())))
        try:
            vcs = asyncio.run(resolve_vcs(payload))
        except Exception:
            vcs = fallback_vcs(payload)
        output = render_statusline(payload, vcs)
    except Exception:
        output = "[idle]"
    print(output)
