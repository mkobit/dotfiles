import sys
import os
from ruff.main import run

if __name__ == "__main__":
    print("Current working directory:", os.getcwd())
    print("Directory contents:", os.listdir("."))
    try:
        run()
    except SystemExit as e:
        sys.exit(e.code)
    # Always exit with 1 to force output to be shown
    sys.exit(1)
