import subprocess
import re
import sys
import os
import click

@click.command()
@click.option('--pane-id', required=True, help='The tmux pane ID to capture')
@click.option('--open-cmd', default=None, help='Command to use to open the URL. If not provided, it will try to guess based on OS.')
def main(pane_id: str, open_cmd: str | None) -> None:
    # Capture pane contents
    try:
        result = subprocess.run(
            ['tmux', 'capture-pane', '-J', '-S', '-', '-t', pane_id, '-p'],
            capture_output=True, text=True, check=True
        )
        scrollback = result.stdout
    except subprocess.CalledProcessError:
        subprocess.run(['tmux', 'display-message', 'Failed to capture pane'])
        sys.exit(1)

    # Find URLs
    url_pattern = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://[a-zA-Z0-9_.~!*'();:@&=+$,/?%#-]+")
    urls = url_pattern.findall(scrollback)

    if not urls:
        subprocess.run(['tmux', 'display-message', 'No URLs found in the current pane.'])
        sys.exit(0)

    # Deduplicate and preserve order (most recent first)
    seen: set[str] = set()
    ordered_urls: list[str] = []
    for url in reversed(urls):
        if url not in seen:
            seen.add(url)
            ordered_urls.append(url)

    # Present URLs using fzf-tmux
    try:
        fzf = subprocess.Popen(
            ['fzf-tmux', '-p', '80%,80%', '--prompt=Open URL: '],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True
        )
        selected_url, _ = fzf.communicate(input='\n'.join(ordered_urls))
        selected_url = selected_url.strip()
    except FileNotFoundError:
        subprocess.run(['tmux', 'display-message', 'fzf-tmux not found.'])
        sys.exit(1)

    if not selected_url:
        sys.exit(0)

    if not open_cmd:
        if sys.platform == 'darwin':
            open_cmd = 'open'
        elif 'microsoft' in os.uname().release.lower():
            open_cmd = 'wslview'
        else:
            open_cmd = 'xdg-open'

    # Process replacement
    try:
        os.execvp(open_cmd, [open_cmd, selected_url])
    except OSError:
        subprocess.run(['tmux', 'display-message', f'Failed to execute {open_cmd}'])
        sys.exit(1)
