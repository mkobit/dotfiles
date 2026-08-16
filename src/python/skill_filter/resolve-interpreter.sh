#!/bin/sh
# Print an absolute path to a real python3 for chezmoi external filter commands.
#
# Called once per template render by .chezmoitemplates/python/filter-interpreter,
# never once per external. Takes the chezmoi destination directory as $1 so it
# stays testable standalone:
#
#   src/python/skill_filter/resolve-interpreter.sh ~
#
# Two rules, both of which exist because they were violated in practice:
#
# 1. Never a bare command name and never a PATH lookup. Both resolve through a
#    version-manager shim on any machine running pyenv or mise. A shim costs
#    ~900ms per spawn against ~30ms for a real interpreter, and these filters run
#    hundreds of times per apply, so a shim turns an apply into minutes of pure
#    process startup. A shim also resolves to whatever version its own config
#    file names, which is state the dotfiles never declared.
# 2. Never a soft feature fallback. skill_filter is stdlib-only and holds a
#    python 3.8 runtime contract, so every candidate below is behaviourally
#    identical and the choice is purely a startup-cost optimization. If the
#    filter ever needs a newer stdlib (tomllib, for instance), raise the floor
#    here and let this script fail rather than letting two different
#    interpreters produce two different results.
#
# Dotfiles-managed interpreters come first because they are the fastest to start
# and are the ones this repo installs, then the system interpreter as the
# always-present floor.
set -eu

dest="${1:?usage: resolve-interpreter.sh <chezmoi-dest-dir>}"

# Newest first, listed explicitly: an alphabetical sort over all matches would
# put cpython-3.8 above cpython-3.14. Glob expansion within a version is
# already sorted, so which patch release wins is deterministic across machines.
for minor in 3.14 3.13 3.12 3.11; do
    for prefix in \
        "$dest/.local/share/uv/python/cpython-$minor" \
        "$dest/.local/share/mise/installs/python/$minor"; do
        # An unmatched glob stays literal, so the -x test simply fails.
        for dir in "$prefix"*; do
            if [ -x "$dir/bin/python3" ]; then
                printf '%s\n' "$dir/bin/python3"
                exit 0
            fi
        done
    done
done

for fallback in /usr/bin/python3 /usr/local/bin/python3; do
    if [ -x "$fallback" ]; then
        printf '%s\n' "$fallback"
        exit 0
    fi
done

echo "resolve-interpreter: no python3 found (looked for uv- and mise-managed 3.11+, then /usr/bin and /usr/local/bin)" >&2
exit 1
