/**
 * See [Git documentation](https://git-scm.com/docs/git-config)
 */
package io.mkobit.git.config

import java.nio.file.Path

private fun prunedMapOf(
  vararg pairs: Pair<String, Any?>
): Map<String, Any> {
  val result = linkedMapOf<String, Any>()
  for ((key, value) in pairs) {
    if (value != null) result[key] = value
  }
  return result.toMap()
}

private fun convertSectionToText(section: Section, subsectionName: String?): String =
  "[${section.name}${subsectionName?.let { sn -> " \"$sn\"" } ?: ""}]" +
    if (section.options.isNotEmpty()) {
      section.options.entries.joinToString(
        separator = System.lineSeparator(),
        prefix = System.lineSeparator(),
      ) {
        "${it.key} = ${it.value}".prependIndent(" ".repeat(4))
      }
    } else {
      System.lineSeparator()
    }

interface Section {
  val name: String
  val options: Map<String, Any>

  fun asText(): String = convertSectionToText(this, null)
}

data class NamedSection(val section: Section, val subsectionName: String) : Section by section {
  override fun asText(): String = convertSectionToText(section, subsectionName)
}

/**
 * @param gpgSign A boolean to specify whether all commits should be GPG signed.
 * Use of this option when doing operations such as rebase can result in a large number of commits being signed.
 * It may be convenient to use an agent to avoid typing your GPG passphrase several times.
 * @param status A boolean to enable/disable inclusion of status information in the commit message template when using an editor to prepare the commit message.
 * Defaults to true.
 */
data class Commit(
  val gpgSign: Boolean? = null,
  val status: Boolean? = null
) : Section {
  override val name: String
    get() = "core"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "gpgSign" to gpgSign,
      "status" to status
    )
}

/**
 * @param eol `auto`, `native`, `true`, `input` or `false`
 */
data class Core(
  val editor: String? = null,
  val excludesFile: Path? = null,
  val eol: String? = null,
  val safecrlf: String? = null
) : Section {
  override val name: String
    get() = "core"
  override val options: Map<String, Any>
    get() = prunedMapOf(
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
  val autoSetUpRebase: AutoSetUpRebase? = null
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
      "autoSetupRebase" to autoSetUpRebase?.name?.toLowerCase()
    )
}

data class Color(
  val ui: Boolean? = null
) : Section {
  override val name: String
    get() = "color"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "ui" to ui
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

// TODO: escape paths in output
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
      "ff" to fastForward?.name?.toLowerCase()
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
      "rebase" to rebase?.name?.toLowerCase()
    )
}

data class Rebase(
  val autoStash: Boolean? = null
) : Section {
  override val name: String
    get() = "rebase"
  override val options: Map<String, Any>
    get() = prunedMapOf(
      "autoStash" to autoStash
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
