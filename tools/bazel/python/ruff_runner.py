import sys
import runpy

if __name__ == "__main__":
    sys.argv[0] = "ruff"
    runpy.run_module("ruff", run_name="__main__")
