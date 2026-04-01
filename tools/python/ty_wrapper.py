import runpy
import sys
import subprocess
import site
import os
import ty._find_ty

if __name__ == "__main__":
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
    sys.exit(subprocess.call([bin_path] + sys.argv[1:]))
