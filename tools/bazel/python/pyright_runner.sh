#!/bin/bash
# This is a simple wrapper for the pyright executable.
# The executable is made available to this script via the `data` attribute
# of the `sh_binary` rule. The path to the executable will be relative
# to the runfiles directory of this script.

# The path to the pyright executable will be something like:
#   <runfiles_dir>/__main__/external/pypi/pyright/pyright
# The exact path can be found by querying the runfiles of this target.
# For now, we assume the executable is on the PATH.
exec pyright "$@"
