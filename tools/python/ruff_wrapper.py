import runpy
import sys

if __name__ == "__main__":
    try:
        runpy.run_module("ruff", run_name="__main__")
    except SystemExit as e:
        sys.exit(e.code)
