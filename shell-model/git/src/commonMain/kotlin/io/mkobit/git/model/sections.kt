/**
 * See [Git documentation](https://git-scm.com/docs/git-config)
 */
package io.mkobit.git.model

import kotlinx.io.files.Path

private fun prunedMapOf(
  vararg pairs: Pair<String, Any?>
): Map<String, Any> {
  val result = linkedMapOf<String, Any>()
  for ((key, value) in pairs) {
    if (value != null) result[key] = value
  }
  return result.toMap()
}

private fun convertSectionToText(section: Section, subsectionName: String?): String = buildString {
  append('[')
  append(section.name)
  if (subsectionName != null) {
    append(" ")
    append('"')
    append(subsectionName)
    append('"')
  }
  append(']')
  section.options.forEach { (k, v) ->
    appendLine()
    append(" ".repeat(4)) // 4x spaces
    append("$k = $v")
  }
}

sealed interface Section {
  val name: String
  val options: Map<String, Any>

  fun asText(): String = convertSectionToText(this, null)
}

fun Section.withName(subsectionName: String) = NamedSection(this, subsectionName)

data class NamedSection(val section: Section, val subsectionName: String) : Section by section {
  override fun asText(): String = convertSectionToText(section, subsectionName)
}

fun Collection<Section>.asText(): String =
  joinToString(separator = "\n", postfix = "\n") { it.asText() }

/**
 * @param gpgSign A boolean to specify whether all commits should be GPG signed.
 * Use of this option when doing operations such as rebase can result in a large number of commits being signed.
 * It may be convenient to use an agent to avoid typing your GPG passphrase several times.
 * @param status A boolean to enable/disable inclusion of status information in the commit message template when using an editor to prepare the commit message.
 * Defaults to true.
 */
data class Commit(
  val gpgSign: Boolean? = null,
  val status: Boolean? = null,
  val verbose: Boolean? = null
) : Section {
  override val name: String
    get() = "commit"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "gpgSign" to gpgSign,
      "status" to status,
      "verbose" to verbose
    )
}

/**
 * See the [git-scm book](https://git-scm.com/docs/git-column).
 */
data class Column(
    val ui: Ui? = null,
) : Section {
  enum class Ui {
    /**
     * Always show in columns
     */
    ALWAYS,

    /**
     * Never show in columns
     */
    NEVER,
    /**
     * show in columns if the output is to the terminal
     */
    AUTO,
  }

  override val name: String
    get() = "column"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "ui" to ui,
    )
}

/**
 * @param autoCrlf
 * @param eol `auto`, `native`, `true`, `input` or `false`
 * @param fsmonitor see [git-config](https://git-scm.com/docs/git-config#Documentation/git-config.txt-corefsmonitor)
 */
data class Core(
  val autoCrlf: AutoCrlf? = null,
  val editor: String? = null,
  val excludesFile: Path? = null,
  val fsmonitor: Boolean? = null,
  val eol: String? = null,
  val safecrlf: String? = null
) : Section {
  override val name: String
    get() = "core"

  /**
   * Setting this variable to "true" is the same as setting the text attribute to "auto" on all files and core.eol to "crlf".
   * Set to true if you want to have CRLF line endings in your working directory and the repository has LF line endings.
   * This variable can be set to input, in which case no output conversion is performed.
   */
  enum class AutoCrlf {
    TRUE,
    FALSE,
    INPUT,
  }

  override val options: Map<String, Any>
    get() = prunedMapOf(
      "autocrlf" to autoCrlf?.name?.lowercase(),
      "editor" to editor,
      "excludesFile" to excludesFile,
      "eol" to eol,
      "safecrlf" to safecrlf,
    )
}

data class User(
  val email: String? = null,
  val userName: String? = null,
  val signingKey: String? = null,
  val useConfigOnly: Boolean? = null
) : Section {

  init {
    email?.let { require(it.isNotBlank()) }
    userName?.let { require(it.isNotBlank()) }
    signingKey?.let { require(it.isNotBlank()) }
  }

  override val name: String
    get() = "user"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "email" to email,
      "name" to userName,
      "signingkey" to signingKey,
      "useConfigOnly" to useConfigOnly
    )
}

// TODO: figure out ! and quoted commands
data class Alias(
  val aliases: Map<String, String>
) : Section {
  override val name: String
    get() = "alias"

  override val options: Map<String, Any>
    get() = aliases
}

data class Branch(
    val autoSetUpRebase: AutoSetUpRebase? = null,
    val sort: String? = null, // todo: change to field names - https://git-scm.com/docs/git-for-each-ref#_field_names
) : Section {
  override val name: String
    get() = "branch"

  /**
   * When a new branch is created with git branch, git switch or git checkout that tracks another branch, this variable tells Git to set up pull to rebase instead of merge (see "branch.<name>.rebase").
   * When `never`, rebase is never automatically set to true.
   * When `local`, rebase is set to true for tracked branches of other local branches.
   * When `remote`, rebase is set to true for tracked branches of remote-tracking branches.
   * When `always`, rebase will be set to true for all tracking branches.
   * See "branch.autoSetupMerge" for details on how to set up a branch to track another branch.
   * This option defaults to never.
   */
  enum class AutoSetUpRebase {
    NEVER,
    LOCAL,
    REMOTE,
    ALWAYS,
  }

  override val options: Map<String, Any>
    get() = prunedMapOf(
      "autoSetupRebase" to autoSetUpRebase?.name?.lowercase(),
      "sort" to sort,
    )
}

// todo: these color options are not correct
data class Color(
  val branch: Boolean? = null,
  val status: Boolean? = null,
  val ui: Boolean? = null,
) : Section {
  override val name: String
    get() = "color"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "branch" to branch,
      "status" to status,
      "ui" to ui,
    )
}

data class Diff(
  val compactionHeuristic: Boolean? = null
) : Section {
  override val name: String
    get() = "diff"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "compactionHeuristic" to compactionHeuristic
    )
}

data class Fetch(
  val prune: Boolean? = null
) : Section {
  override val name: String
    get() = "fetch"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "prune" to prune
    )
}

data class Gpg(
  val program: String? = null
) : Section {
  override val name: String
    get() = "gpg"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "program" to program
    )
}

data class Init(
  val defaultBranch: String? = null
) : Section {
  override val name: String
    get() = "init"
  override val options: Map<String, Any>
    get() = prunedMapOf("defaultBranch" to defaultBranch)
}

// TODO: escape paths in output
// TODO: better handle include dirs that should be suffixed with '/' since that translates to '/**'
sealed class Include : Section {
  abstract val path: Path

  companion object {
    operator fun invoke(path: Path): Include = IncludePattern(path)
  }

  override val options: Map<String, Any>
    get() = mapOf(
      "path" to path
    )

  private data class IncludePattern(override val path: Path) : Include() {
    override val name: String
      get() = "include"
  }

  private data class IncludeIfGitDir(override val path: Path, val gitDirPattern: Path) : Include() {
    override val name: String
      get() = "includeIf"
  }

  private data class IncludeIfOnBranch(override val path: Path, val branchPattern: String) : Include() {
    override val name: String
      get() = "includeIf"
  }

  fun ifGitDir(gitDirPattern: Path): NamedSection = NamedSection(IncludeIfGitDir(path, gitDirPattern), "gitdir:$gitDirPattern")
  fun ifOnBranch(branchPattern: String): NamedSection = NamedSection(IncludeIfOnBranch(path, branchPattern), "onbranch:$branchPattern")
}

data class Interactive(
  val diffFilter: String? = null
) : Section {
  override val name: String
    get() = "interactive"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "diffFilter" to diffFilter
    )
}

data class Merge(
  val fastForward: FastForward? = null
) : Section {
  enum class FastForward {
    TRUE,
    FALSE,
    ONLY
  }

  override val name: String
    get() = "merge"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "ff" to fastForward?.name?.lowercase()
    )
}

data class Pager(
  val log: String? = null,
  val show: String? = null,
  val diff: String? = null,
) : Section {
  override val name: String
    get() = "pager"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "diff" to diff,
      "log" to log,
      "show" to show
    )
}

data class Pull(
  val rebase: Rebase? = null
) : Section {
  override val name: String
    get() = "pull"

  /**
   * When `true`, rebase branches on top of the fetched branch, instead of merging the default branch from the default remote when "git pull" is run.
   * See "branch.<name>.rebase" for setting this on a per-branch basis.
   *
   * When `merges` (or just **m**), pass the `--rebase-merges` option to **git rebase** so that the local merge commits are included in the rebase (see git-rebase[1] for details).
   *
   * When `preserve` (or just **p**, deprecated in favor of `merges`), also pass `--preserve-merges` along to git rebase so that locally committed merge commits will not be flattened by running **git pull**.
   *
   * When the value is `interactive` (or just **i**), the rebase is run in interactive mode.
   */
  enum class Rebase {
    TRUE,
    FALSE,
    MERGES,
    PRESERVE,
    INTERACTIVE
  }
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "rebase" to rebase?.name?.lowercase()
    )
}

data class Push(
  val default: Default? = null
) : Section {
  override val name: String
    get() = "push"

  /**
   * Defines the action `git push` should take if no refspec is given (whether from the command-line, config, or elsewhere).
   * Different values are well-suited for specific workflows; for instance, in a purely central workflow (i.e. the fetch source is equal to the push destination), `upstream` is probably what you want.
   *
   */
  enum class Default {
    /**
     * do not push anything (error out) unless a refspec is given.
     * This is primarily meant for people who want to avoid mistakes by always being explicit.
     */
    NOTHING,

    /**
     * push the current branch to update a branch with the same name on the receiving end.
     * Works in both central and non-central workflows.
     */
    CURRENT,

    /**
     * push the current branch back to the branch whose changes are usually integrated into the current branch (which is called `@{upstream}`).
     * This mode only makes sense if you are pushing to the same repository you would normally pull from (i.e. central workflow).
     */
    UPSTREAM,

    /**
     * This is a deprecated synonym for [UPSTREAM].
     */
    TRACKING,

    /**
     * in centralized workflow, work like upstream with an added safety to refuse to push if the upstream branch’s name is different from the local one.
     * When pushing to a remote that is different from the remote you normally pull from, work as current.
     * This is the safest option and is suited for beginners.
     *
     * This mode has become the default in Git 2.0.
     */
    SIMPLE,

    /**
     * push all branches having the same name on both ends.
     * This makes the repository you are pushing to remember the set of branches that will be pushed out (e.g. if you always push maint and master there and no other branches, the repository you push to will have these two branches, and your local maint and master will be pushed there).
     * To use this mode effectively, you have to make sure all the branches you would push out are ready to be pushed out before running git push, as the whole point of this mode is to allow you to push all of the branches in one go. If you usually finish work on only one branch and push out the result, while other branches are unfinished, this mode is not for you. Also this mode is not suitable for pushing into a shared central repository, as other people may add new branches there, or update the tip of existing branches outside your control.
     * This used to be the default, but not since Git 2.0 ([SIMPLE] is the new default).
     */
    MATCHING
  }

  override val options: Map<String, Any>
    get() = prunedMapOf(
      "default" to default?.name?.lowercase()
    )
}

data class Rebase(
  val autoStash: Boolean? = null,
  val autoSquash: Boolean? = null
) : Section {
  override val name: String
    get() = "rebase"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "autoSquash" to autoSquash,
      "autoStash" to autoStash
    )
}

data class Rerere(
  val enabled: Boolean? = null,
  val autoUpdate: Boolean? = null
) : Section {
  override val name: String
    get() = "rerere"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "autoUpdate" to autoUpdate,
      "enabled" to enabled
    )
}

data class Stash(
  val showPatch: Boolean? = null
) : Section {
  override val name: String
    get() = "stash"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "showPatch" to showPatch
    )
}

data class Tag(
  val gpgSign: Boolean? = null
) : Section {
  override val name: String
    get() = "tag"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "gpgSign" to gpgSign
    )
}
