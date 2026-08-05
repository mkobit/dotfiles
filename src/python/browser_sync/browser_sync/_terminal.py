"""Terminal I/O for browser-sync: colored logging and raw-tty prompts."""

import logging
import sys
import termios
import time
import tty
import typing
from collections.abc import Callable

OK = 25
logging.addLevelName(OK, "OK")
_log = logging.getLogger(__name__)


class _ColorFormatter(logging.Formatter):
    """Terminal formatter with colored level badges and timestamps."""

    _COLORS: typing.ClassVar[dict[int, str]] = {
        logging.INFO: "\033[0;34m",
        OK: "\033[0;32m",
        logging.WARNING: "\033[0;33m",
        logging.ERROR: "\033[0;31m",
    }
    _LABELS: typing.ClassVar[dict[int, str]] = {
        logging.INFO: "INFO",
        OK: "OK  ",
        logging.WARNING: "WARN",
        logging.ERROR: "ERR ",
    }

    @typing.override
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with timestamp and colored badge."""
        ts = time.strftime("%H:%M:%S")
        color = self._COLORS.get(record.levelno, "\033[0m")
        label = self._LABELS.get(record.levelno, record.levelname)
        return f"\033[2m{ts}\033[0m {color}[{label}]\033[0m {record.getMessage()}"


def setup_logging() -> None:
    """Install the colored formatter on the root logger."""
    handler = logging.StreamHandler()
    handler.setFormatter(_ColorFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])


def getkey() -> str:
    """Read a single keypress from stdin in raw mode."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def prompt_enter(message: str) -> None:
    """Wait for Enter; exit cleanly on Ctrl+C."""
    print(f"\033[0;36m[?]\033[0m    {message}", end="", flush=True)
    while True:
        ch = getkey()
        if ch in ("\r", "\n"):
            print()
            return
        if ch == "\x03":
            print()
            _log.info("skipped")
            sys.exit(0)


def prompt_done_or_recopy(copy_fn: Callable[[], None]) -> None:
    """Wait for Enter (done) or 'r' (recopy the clipboard payload)."""
    print("\033[0;36m[?]\033[0m    Press Enter when done, or 'r' to recopy ", end="", flush=True)
    while True:
        ch = getkey()
        if ch in ("\r", "\n"):
            print()
            return
        if ch.lower() == "r":
            copy_fn()
            print()
            _log.log(OK, "recopied to clipboard")
            print("\033[0;36m[?]\033[0m    Press Enter when done, or 'r' to recopy ", end="", flush=True)
        if ch == "\x03":
            print()
            _log.info("skipped")
            sys.exit(0)


def _shortcut_sync_mode_for_key(key: str) -> str | None:
    """Return the payload mode selected by a shortcut-sync keypress."""
    if key in ("\r", "\n"):
        return "prune"
    if key.lower() == "x":
        return "exclude_removals"
    if key.lower() == "d":
        return "dry_run"
    return None


def prompt_shortcut_sync_mode() -> str:
    """Choose the Chrome shortcuts sync payload to copy."""
    print(
        "\033[0;33m[!]\033[0m    Enter: sync + prune, 'x': sync without removals, 'd': dry run ",
        end="",
        flush=True,
    )
    while True:
        ch = getkey()
        if mode := _shortcut_sync_mode_for_key(ch):
            print()
            return mode
        if ch == "\x03":
            print()
            _log.info("skipped")
            sys.exit(0)
