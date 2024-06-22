package io.mkobit.homedir.assembler.git

import io.mkobit.git.model.Alias
import io.mkobit.git.model.Branch
import io.mkobit.git.model.Color
import io.mkobit.git.model.Column
import io.mkobit.git.model.Commit
import io.mkobit.git.model.Core
import io.mkobit.git.model.Diff
import io.mkobit.git.model.Fetch
import io.mkobit.git.model.Help
import io.mkobit.git.model.Init
import io.mkobit.git.model.Interactive
import io.mkobit.git.model.Merge
import io.mkobit.git.model.Pager
import io.mkobit.git.model.Pull
import io.mkobit.git.model.Push
import io.mkobit.git.model.Rebase
import io.mkobit.git.model.Rerere
import io.mkobit.git.model.Section
import io.mkobit.git.model.Stash
import okio.Path
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds

internal fun generalGitConfig(
  excludesFile: Path
): List<Section> = buildList {
  add(
    Alias(
      mapOf(
        "aliases" to "! git var -l | grep --color=never -e '^alias' | sed -E 's/^alias.//g'",
        "amend" to "commit --amend",
        "branches" to "branch -a",
        "delete-merged-branches" to "\"!git checkout master && git branch --merged master | sed -E 's/^\\\\*//;s/\\\\s*//' | grep -v 'master' | xargs --no-run-if-empty --max-args 1 git branch -d\"",
        "diff-staged" to "diff --cached",
        "exec" to "! exec", // Exec a command from root of git repository - http://stackoverflow.com/a/957978/627727
        "graph-all" to "log --color --date-order --graph --oneline --decorate --simplify-by-decoration --all",
        "please" to "push --force-with-lease",
        "touchup" to "!git add -u && git commit --amend --no-edit",
        "sync" to "pull --rebase --autostash",
        "unstage" to "reset HEAD --",
        "rename-branch" to "branch -mv",
        "root" to "! pwd",
        "amendit" to "commit --amend --no-edit",
        "clean-all" to "clean -d -x -f",
        "wip" to "commit -anm 'WIP'",
      )
    )
  )
  add(
    Alias(
      mapOf(
        "a" to "add",
        "au" to "add -u",
        "st" to "status",
        "lg" to "log --graph --pretty=format:'%C(yellow)%h%C(cyan)%d%Creset %s %C(white)- %an, %ar%Creset'",
        "ll" to "log --stat --abbrev-commit",
        "cm" to "commit",
        "co" to "checkout",
        "cob" to "checkout -b"
      )
    )
  )
  add(
    Branch(
      autoSetUpRebase = Branch.AutoSetUpRebase.ALWAYS,
      sort = "-committerdate", // reverse committer date
    )
  )
  add(
    Color(
      branch = true,
      status = true,
      ui = true,
    )
  )
  add(
    Column(
      ui = Column.Ui.AUTO,
    )
  )
  add(
    Commit(
      verbose = true,
    )
  )
  add(
    Core(
      autoCrlf = Core.AutoCrlf.INPUT,
      editor = "vim",
      excludesFile = excludesFile,
      fsmonitor = true,
    )
  )
  add(
    Diff(
      compactionHeuristic = true,
    )
  )
  add(
    Fetch(
      prune = true,
    )
  )
  add(
    Help(
      autocorrect = 1.seconds + 500.milliseconds,
    )
  )
  add(
    Init(
      defaultBranch = "main"
    )
  )
  add(
    Merge(
      fastForward = Merge.FastForward.FALSE,
      conflictStyle = Merge.ConflictStyle.ZDIFF3,
    )
  )
  add(
    Pull(
      rebase = Pull.Rebase.TRUE,
    )
  )
  add(
    Push(
      default = Push.Default.CURRENT,
    )
  )
  add(
    Rebase(
      autoSquash = true,
      autoStash = true,
    )
  )
  add(
    Rerere(
      autoUpdate = true,
      enabled = true,
    )
  )
  add(
    Stash(
      showPatch = true,
    )
  )
}
