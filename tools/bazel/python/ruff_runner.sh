#!/bin/bash
set -e
RUFF_EXEC_PATH="external/pypi/ruff/ruff"
if [ ! -f "$RUFF_EXEC_PATH" ]; then
    RUFF_EXEC_PATH="external/rules_python_pip_pypi_313_ruff/ruff"
fi

"$RUFF_EXEC_PATH" "$@"
