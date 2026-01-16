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
        from python.runfiles import runfiles  # noqa: F401
    except ImportError:
        # Fallback to local copy or nothing
        runfiles = None


def find_ruff_binary(runfiles_dir: str | None) -> list[str]:
    candidates = []

    # Optimized search: look for ruff repo in top level or inside known structure
    # We expect the ruff binary to be in <repo>/bin/ruff
    if runfiles_dir and os.path.exists(runfiles_dir):
        # Scan top level directories
        for entry in os.scandir(runfiles_dir):
            if entry.is_dir() and "ruff" in entry.name:
                # Check for bin/ruff
                bin_ruff = os.path.join(entry.path, "bin", "ruff")
                if os.access(bin_ruff, os.X_OK):
                    candidates.append(bin_ruff)
                    break

    # Fallback to limited depth walk if not found
    if not candidates and runfiles_dir and os.path.exists(runfiles_dir):
        for root, dirs, files in os.walk(runfiles_dir):
            # Optimization: Don't go too deep
            # Calculate depth relative to runfiles_dir
            rel_path = os.path.relpath(root, runfiles_dir)
            if rel_path == ".":
                depth = 0
            else:
                depth = len(rel_path.split(os.sep))

            if depth > 2:
                del dirs[:]  # Stop recursing
                continue

            if "ruff" in files:
                path = os.path.join(root, "ruff")
                if os.access(path, os.X_OK) and os.path.basename(root) == "bin":
                    candidates.append(path)
                    break

    return candidates


def main() -> None:
    # Initialize runfiles
    r = None
    if runfiles:
        r = runfiles.Create()

    if not r:
        print("Warning: Could not initialize runfiles library.", file=sys.stderr)

    # We need to find the 'ruff' binary.
    runfiles_dir = os.environ.get("RUNFILES_DIR")
    if not runfiles_dir and r:
        runfiles_dir = r.EnvVar("RUNFILES_DIR")

    if not runfiles_dir:
        runfiles_dir = os.environ.get("JAVA_RUNFILES")

    candidates = find_ruff_binary(runfiles_dir)

    if not candidates:
        print(
            f"Error: Could not find 'ruff' binary. RUNFILES_DIR={runfiles_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    ruff_bin = candidates[0]

    # Execute ruff
    args = [ruff_bin] + sys.argv[1:]
    os.execv(ruff_bin, args)


if __name__ == "__main__":
    main()
