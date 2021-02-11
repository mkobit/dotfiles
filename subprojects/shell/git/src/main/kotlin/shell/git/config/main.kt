@file:JvmName("Main")

package shell.git.config

import io.mkobit.git.config.Alias
import io.mkobit.git.config.Branch
import io.mkobit.git.config.Color
import io.mkobit.git.config.Commit
import io.mkobit.git.config.Core
import io.mkobit.git.config.Diff
import io.mkobit.git.config.Fetch
import io.mkobit.git.config.Gpg
import io.mkobit.git.config.Interactive
import io.mkobit.git.config.Merge
import io.mkobit.git.config.Pager
import io.mkobit.git.config.Pull
import io.mkobit.git.config.Push
import io.mkobit.git.config.Rebase
import io.mkobit.git.config.Rerere
import io.mkobit.git.config.Section
import io.mkobit.git.config.Stash
import io.mkobit.git.config.User
import io.mkobit.git.config.asText
import picocli.CommandLine
import java.nio.file.Path
import java.util.concurrent.Callable
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.Path
import kotlin.io.path.div
import kotlin.io.path.writeText
import kotlin.system.exitProcess

@CommandLine.Command(
  name = "generateGitConfig",
  mixinStandardHelpOptions = true,
)
@ExperimentalPathApi
internal class GenerateGitConfig : Callable<Int> {

  @CommandLine.Option(
    names = ["--outputDir"],
    required = true
  )
  lateinit var outputDir: Path

  override fun call(): Int {
    val general = outputDir / "gitconfig_general"
    general.writeText(generalGitConfig().asText())
    val personal = outputDir / "gitconfig_personal"
    personal.writeText(personalGitConfig().asText())
    return 0
  }
}

@ExperimentalPathApi
private fun generalGitConfig(): List<Section> = listOf(
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
      "wip" to "commit -anm 'WIP'"
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
    autoSetUpRebase = Branch.AutoSetUpRebase.ALWAYS
  ),
  Color(
    ui = true
  ),
  Commit(
    verbose = true
  ),
  Core(
    autoCrlf = Core.AutoCrlf.INPUT,
    editor = "vim",
    excludesFile = Path("~/.gitignore_global")
  ),
  Diff(
    compactionHeuristic = true
  ),
  Fetch(
    prune = true
  ),
  Interactive(
    diffFilter = "diff-highlight"
  ),
  Merge(
    fastForward = Merge.FastForward.FALSE
  ),
  Pager(
    log = "diff-highlight | less",
    show = "diff-highlight | less",
    diff = "diff-highlight | less"
  ),
  Pull(
    rebase = Pull.Rebase.TRUE
  ),
  Push(
    default = Push.Default.SIMPLE
  ),
  Rebase(
    autoSquash = true,
    autoStash = true,
  ),
  Rerere(
    enabled = true
  ),
  Stash(
    showPatch = true
  )
)

@ExperimentalPathApi
private fun personalGitConfig(): List<Section> = listOf(
  Commit(
    gpgSign = true
  ),
  Gpg(
    program = "gpg2"
  ),
  User(
    email = "mkobit@gmail.com",
    userName = "Mike Kobit",
    signingKey = "1698254E135D7ADE!"
  )
)

@ExperimentalPathApi
fun main(args: Array<String>): Unit = exitProcess(CommandLine(GenerateGitConfig()).execute(*args))
