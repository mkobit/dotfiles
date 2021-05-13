package dotfiles.shell.git

import io.mkobit.git.config.Alias
import io.mkobit.git.config.Branch
import io.mkobit.git.config.Color
import io.mkobit.git.config.Commit
import io.mkobit.git.config.Core
import io.mkobit.git.config.Diff
import io.mkobit.git.config.Fetch
import io.mkobit.git.config.Interactive
import io.mkobit.git.config.Merge
import io.mkobit.git.config.Pager
import io.mkobit.git.config.Pull
import io.mkobit.git.config.Push
import io.mkobit.git.config.Rebase
import io.mkobit.git.config.Rerere
import io.mkobit.git.config.Section
import io.mkobit.git.config.Stash
import java.nio.file.Path

internal fun generalGitConfig(excludesFile: Path): List<Section> = listOf(
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
      "soft-reset" to "!git reset --soft HEAD~1 && git reset HEAD .",
      "touchup" to "!git add -u && git commit --amend --no-edit",
      "sync" to "pull --rebase --autostash",
      "unstage" to "reset HEAD --",
      "rename-branch" to "branch -mv",
      "root" to "! pwd",
      "amendit" to "commit --amend --no-edit",
      "clean-all" to "clean -d -x -f",
      "wip" to "commit -anm 'WIP'",
    )
  ),
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
  ),
  Branch(
    autoSetUpRebase = Branch.AutoSetUpRebase.ALWAYS,
  ),
  Color(
    branch = true,
    status = true,
    ui = true,
  ),
  Commit(
    verbose = true,
  ),
  Core(
    autoCrlf = Core.AutoCrlf.INPUT,
    editor = "vim",
    excludesFile = excludesFile,
  ),
  Diff(
    compactionHeuristic = true,
  ),
  Fetch(
    prune = true,
  ),
  Interactive(
    diffFilter = diffProgram
  ),
  Merge(
    fastForward = Merge.FastForward.FALSE,
  ),
  Pager(
    log = "$diffProgram | less",
    show = "$diffProgram | less",
    diff = "$diffProgram | less",
  ),
  Pull(
    rebase = Pull.Rebase.TRUE,
  ),
  Push(
    default = Push.Default.SIMPLE,
  ),
  Rebase(
    autoSquash = true,
    autoStash = true,
  ),
  Rerere(
    autoUpdate = true,
    enabled = true,
  ),
  Stash(
    showPatch = true,
  )
)

private val diffProgram: String by lazy {
  val os = System.getProperty("os.name").lowercase()
  when {
    listOf("mac os x", "darwin", "osx").any { os.contains(it) } -> "/usr/local/opt/git/share/git-core/contrib/diff-highlight/diff-highlight" // todo: locate dynamically
    os.contains("linux") -> "diff" // todo: figure out better way to install diff-highlight for ubuntu
    else -> TODO("unsupported operating system $os")
  }
//  "diff-highlight"
}
