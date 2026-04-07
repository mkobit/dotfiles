import os
import subprocess
import sys

if __name__ == "__main__":
    import ty._find_ty

    try:
        bin_path = ty._find_ty.find_ty_bin()
    except ty._find_ty.TyNotFound:
        # Avoid recursive glob which hangs in Bazel sandbox.
        # Based on Bazel runfiles structure observed for rules_python:
        # ty file=.../ty.runfiles/.../site-packages/ty/__init__.py
        # Binary is at: .../ty.runfiles/rules_python++pip+pypi_314_ty/bin/ty
        base_dir = os.path.dirname(os.path.abspath(ty._find_ty.__file__))
        site_packages_dir = os.path.dirname(base_dir)
        repo_dir = os.path.dirname(site_packages_dir)
        possible_paths = [
            os.path.join(repo_dir, "bin", "ty"),
            os.path.join(repo_dir, "data", "bin", "ty"),
            os.path.join(repo_dir, "data", "scripts", "ty"),
        ]
        bin_path = next((p for p in possible_paths if os.path.isfile(p)), None)

        if not bin_path:
            import shutil

            bin_path = shutil.which("ty")

        if not bin_path:
            print(
                "Could not find ty binary via ty module or PATH"
                " (avoided expensive glob).",
                file=sys.stderr,
            )
            sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()

    env = os.environ.copy()
    # Restrict Ty to single thread to prevent CPU lockups/hanging under Bazel sandbox
    env["RAYON_NUM_THREADS"] = "1"

    try:
        os.execve(bin_path, [bin_path] + sys.argv[1:], env)
    except BlockingIOError:
        # Fallback for macOS sandbox limits
        res = subprocess.run([bin_path] + sys.argv[1:], env=env)
        sys.exit(res.returncode)
    except Exception as e:
        print(f"Exception when calling ty: {e}", file=sys.stderr)
        sys.exit(1)
