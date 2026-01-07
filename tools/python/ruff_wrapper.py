import os
import sys

# To import runfiles, we need to add the imports from the runfiles target.
# rules_python's runfiles library sets imports=["../.."] which usually means
# we can import "rules_python.python.runfiles.runfiles".
try:
    from rules_python.python.runfiles import runfiles
except ImportError:
    # Try different fallback if mapped differently
    try:
        from python.runfiles import runfiles
    except ImportError:
        # Fallback to local copy or nothing
        runfiles = None


def main() -> None:
    # Initialize runfiles
    r = None
    if runfiles:
        r = runfiles.Create()

    if not r:
        print("Warning: Could not initialize runfiles library.", file=sys.stderr)
        # Fallback logic below...

    # We need to find the 'ruff' binary.
    runfiles_dir = os.environ.get("RUNFILES_DIR")
    if not runfiles_dir and r:
        runfiles_dir = r.EnvVar("RUNFILES_DIR")

    if not runfiles_dir:
        runfiles_dir = os.environ.get("JAVA_RUNFILES")

    candidates = []

    # Method 1: Use Rlocation if available
    # We need the exact repo name.
    # Try to find a file we know exists to deduce the repo name?
    # Or just search directory structure.

    if runfiles_dir and os.path.exists(runfiles_dir):
        # We can walk the runfiles directory
        for root, _dirs, files in os.walk(runfiles_dir):
            if "ruff" in files:
                # Check if this looks like the binary we want
                # It should be in a 'bin' directory and executable
                path = os.path.join(root, "ruff")
                if os.access(path, os.X_OK) and os.path.basename(root) == "bin":
                    candidates.append(path)

    if not candidates:
        print(
            f"Error: Could not find 'ruff' binary. RUNFILES_DIR={runfiles_dir}",
            file=sys.stderr
        )
        sys.exit(1)

    ruff_bin = candidates[0]

    # Execute ruff
    # We need to pass all arguments
    args = [ruff_bin] + sys.argv[1:]

    os.execv(ruff_bin, args)


if __name__ == "__main__":
    main()
