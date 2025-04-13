"""
Example of a Git module extension for ZSH.
This demonstrates how other modules can provide ZSH configuration.
"""

load("//modules/zsh:zsh.bzl", "zsh_extension")

def git_zsh_extension():
    """Creates a ZSH extension for Git functionality."""
    return zsh_extension(
        name = "git_zsh_ext",
        type = "git",
        source = "//modules/git",
        aliases = {
            "g": "git",
            "ga": "git add",
            "gc": "git commit -v",
            "gco": "git checkout",
            "gd": "git diff",
            "gl": "git pull",
            "gp": "git push",
            "gs": "git status",
            "gpr": "git pull --rebase",
        },
        functions = {
            "git_current_branch": "git branch --show-current 2>/dev/null",
            "git_main_branch": """
local ref
for ref in refs/heads/main refs/heads/trunk refs/heads/mainline refs/heads/default refs/heads/master; do
  if git show-ref -q --verify $ref; then
    echo ${ref:11}
    return 0
  fi
done
echo master
return 1
""",
            "git_develop_branch": """
local ref
for ref in refs/heads/develop refs/heads/development refs/heads/devel; do
  if git show-ref -q --verify $ref; then
    echo ${ref:11}
    return 0
  fi
done
echo develop
return 1
""",
        },
        env_vars = {
            "GIT_EDITOR": "vim",
        },
    )