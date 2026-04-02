import sys
import subprocess
import site
import os

if __name__ == "__main__":
    import ty._find_ty

    try:
        bin_path = ty._find_ty.find_ty_bin()
    except ty._find_ty.TyNotFound:
        base_dir = os.path.dirname(os.path.abspath(ty._find_ty.__file__))
        site_packages_dir = os.path.dirname(base_dir)
        wheel_dir = os.path.dirname(site_packages_dir)
        possible_paths = [
            os.path.join(wheel_dir, "data", "scripts", "ty"),
            os.path.join(wheel_dir, "bin", "ty"),
            os.path.join(site_packages_dir, "bin", "ty"),
            os.path.join(wheel_dir, "data", "bin", "ty"),
        ]
        bin_path = next((p for p in possible_paths if os.path.isfile(p)), None)
        if not bin_path:
            import glob

            search_dir = os.path.dirname(os.path.dirname(wheel_dir))
            found = glob.glob(os.path.join(search_dir, "**", "ty"), recursive=True)
            bin_path = next(
                (f for f in found if os.path.isfile(f) and os.access(f, os.X_OK)), None
            )
        if not bin_path:
            import shutil

            bin_path = shutil.which("ty")
        if not bin_path:
            print("Could not find ty binary via ty module or PATH.", file=sys.stderr)
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
