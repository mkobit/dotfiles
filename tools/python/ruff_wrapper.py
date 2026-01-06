import os
import sys


def main() -> None:
    # We need to find the 'ruff' binary.
    # It is located at 'rules_python++pip+pypi_313_ruff/bin/ruff' (or similar).
    # Since the exact repo name might change, we search for 'bin/ruff'.

    runfiles_dir = os.environ.get("RUNFILES_DIR")
    if not runfiles_dir:
        # Fallback
        runfiles_dir = os.environ.get("JAVA_RUNFILES")

    if not runfiles_dir:
        # Try to deduce from argv[0] which is typically the script path
        # When running in sandbox:
        # sys.argv[0] is typically /path/to/sandbox/.../bin/tools/python/ruff
        # runfiles are at /path/to/sandbox/.../bin/tools/python/ruff.runfiles

        candidate = sys.argv[0] + ".runfiles"
        if os.path.exists(candidate):
            runfiles_dir = candidate

    # Search for bin/ruff
    candidates = []
    if runfiles_dir and os.path.exists(runfiles_dir):
        for root, _dirs, files in os.walk(runfiles_dir):
            if "ruff" in files and os.path.basename(root) == "bin":
                candidates.append(os.path.join(root, "ruff"))

    if not candidates:
        print(f"Error: Could not find 'ruff' binary in runfiles: {runfiles_dir}",
              file=sys.stderr)
        sys.exit(1)

    ruff_bin = candidates[0]

    # Execute ruff
    # We need to pass all arguments
    args = [ruff_bin] + sys.argv[1:]

    os.execv(ruff_bin, args)


if __name__ == "__main__":
    main()
