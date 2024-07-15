from pathlib import Path
from typing import List
from datetime import timedelta

from src.dotfiles.git.config import (
    Alias,
    Branch,
    Color,
    Column,
    Commit,
    Core,
    Diff,
    Fetch,
    Help,
    Init,
    Merge,
    Pull,
    Push,
    Rebase,
    Rerere,
    Section,
    Stash,
)


def general_git_config(excludes_file: Path) -> List[Section]:
    general = [
        Alias(
            {
                "aliases": "! git var -l | grep --color=never -e '^alias' | sed -E 's/^alias.//g'",
                "amend": "commit --amend",
                "branches": "branch -a",
                "delete-merged-branches": "\"!git checkout master && git branch --merged master | sed -E 's/^\\\\*//;s/\\\\s*//' | grep -v 'master' | xargs --no-run-if-empty --max-args 1 git branch -d\"",
                "diff-staged": "diff --cached",
                "exec": "! exec",  # Exec a command from root of git repository - http://stackoverflow.com/a/957978/627727
                "graph-all": "log --color --date-order --graph --oneline --decorate --simplify-by-decoration --all",
                "please": "push --force-with-lease",
                "touchup": "!git add -u && git commit --amend --no-edit",
                "sync": "pull --rebase --autostash",
                "unstage": "HEAD --",
                "rename-branch": "branch -mv",
                "root": "pwd",
                "amendit": "commit --amend --no-edit",
                "clean-all": "clean -d -x -f",
                "wip": "commit -anm 'WIP'",
            }
        ),
        Alias(
            {
                "a": "add",
                "au": "add -u",
                "st": "status",
                "lg": "log --graph --pretty=format:'%C(yellow)%h%C(cyan)%d%Creset %s %C(white)- %an, %ar%Creset'",
                "ll": "log --stat --abbrev-commit",
                "cm": "commit",
                "co": "checkout",
                "cob": "checkout -b",
            }
        ),
        Branch(
            auto_set_up_rebase="always",
            sort="-committerdate",  # reverse committer date
        ),
        Color(
            branch=True,
            status=True,
            ui=True,
        ),
        Column(
            ui="auto",
        ),
        Commit(
            verbose=True,
        ),
        Core(
            autocrlf="input",
            editor="vim",
            excludes_file=excludes_file,
            fsmonitor=True,
        ),
        Diff(
            compaction_heuristic=True,
        ),
        Fetch(
            prune=True,
        ),
        Help(
            autocorrect=timedelta(seconds=3),
        ),
        Init(default_branch="main"),
        Merge(
            ff=False,
            conflict_style="zdiff3",
        ),
        Pull(
            rebase=True,
        ),
        Push(
            default="current",
        ),
        Rebase(
            auto_squash=True,
            auto_stash=True,
        ),
        Rerere(
            auto_update=True,
            enabled=True,
        ),
        Stash(
            show_patch=True,
        ),
    ]
    return general
