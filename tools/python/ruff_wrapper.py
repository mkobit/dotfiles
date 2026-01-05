import runpy
import sys

if __name__ == "__main__":
    # Ruff's __main__ usually performs an execv, replacing the process
    # We use runpy to execute it as if `python -m ruff` was called
    try:
        runpy.run_module("ruff", run_name="__main__")
    except SystemExit as e:
        sys.exit(e.code)
