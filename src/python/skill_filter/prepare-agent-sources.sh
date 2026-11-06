#!/bin/sh
# Publish generated agent source entries into a chezmoi source root.
#
#   prepare-agent-sources.sh <source-root> [<dest-dir>]
#
# Runs as a chezmoi hook and from bin/assemble, before uv or mise exist, so it
# resolves a real python3 with resolve-interpreter.sh and runs the stdlib-only
# module with -S. The module takes its own lock and publishes all-or-nothing.
set -eu

here="$(cd "$(dirname "$0")" && pwd)"
source_root="${1:?usage: prepare-agent-sources.sh <source-root> [<dest-dir>]}"
dest="${2:-${CHEZMOI_DEST_DIR:-/nonexistent}}"
# resolve-interpreter.sh is not executable in git; run it with sh, as the
# python/filter-interpreter template does.
python="$(sh "$here/resolve-interpreter.sh" "$dest")"
exec "$python" -S "$here/skill_filter/agent_sources.py" prepare --source-root "$source_root"
