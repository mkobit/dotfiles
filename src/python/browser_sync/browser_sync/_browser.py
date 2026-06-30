"""Browser sync targets and launching."""

import enum
import subprocess


class Browser(enum.Enum):
    """A browser sync target."""

    CHROME = "chrome"
    FIREFOX = "firefox"


def resolve_targets(*, chrome: bool, firefox: bool) -> tuple[Browser, ...]:
    """Resolve --chrome/--firefox flags to target browsers; default Chrome."""
    selected = tuple(browser for browser, enabled in ((Browser.CHROME, chrome), (Browser.FIREFOX, firefox)) if enabled)
    return selected or (Browser.CHROME,)


def open_in_chrome(url: str) -> None:
    """Open a URL in Google Chrome."""
    subprocess.run(["open", "-a", "Google Chrome", url], check=True)
