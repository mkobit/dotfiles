import sys
if sys.version_info >= (3, 11):
    import tomllib
    import json

    toml_str = """
[settings]
"npm.package_manager" = "pnpm"
"""
    try:
        data = tomllib.loads(toml_str)
        print("OK: ", data)
    except Exception as e:
        print("ERROR:", e)
