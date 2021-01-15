package io.mkobit.git.config

import org.junit.jupiter.api.Nested
import org.junit.jupiter.api.Test
import strikt.api.expectThat
import strikt.assertions.containsExactly
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.Path

internal class GitConfigTest {
  @Test
  internal fun `named section as text`() {
    val subject = NamedSection(
      User(
        userName = "mike.kobit",
        email = "mike.kobit@example.com"
      ),
      "myusersubsection"
    )
    expectThat(subject.asText().lines())
      .containsExactly(
        """[user "myusersubsection"]""",
        "    email = mike.kobit@example.com",
        "    name = mike.kobit",
      )
  }

  @Test
  internal fun `alias section as text`() {
    val subject = Alias(
      mapOf(
        "aa" to "add --all",
        "amend" to "commit --amend",
        "soft-reset" to "!git reset --soft HEAD~1 && git reset HEAD .",
        "wip" to "commit -am 'WIP'"
      )
    )

    expectThat(subject.asText().lines())
      .containsExactly(
        "[alias]",
        "    aa = add --all",
        "    amend = commit --amend",
        "    soft-reset = !git reset --soft HEAD~1 && git reset HEAD .",
        "    wip = commit -am 'WIP'",
      )
  }

  @ExperimentalPathApi
  @Nested
  internal inner class IncludeTest {

    @Test
    internal fun `include path`() {
      val subject = Include(Path("~/.my_git_config"))
      expectThat(subject.asText().lines())
        .containsExactly(
          "[include]",
          "    path = ~/.my_git_config"
        )
    }

    @Test
    internal fun `includeIf gitdir`() {
      val subject = Include(Path("~/.my_git_config")).ifGitDir(Path("/path/to/group"))

      expectThat(subject.asText().lines())
        .containsExactly(
          "[includeIf \"gitdir:/path/to/group\"]",
          "    path = ~/.my_git_config"
        )
    }

    @Test
    internal fun `includeIf onbranch`() {
      val subject = Include(Path("~/.my_git_config")).ifOnBranch("mybranch/**")

      expectThat(subject.asText().lines())
        .containsExactly(
          "[includeIf \"onbranch:mybranch/**\"]",
          "    path = ~/.my_git_config"
        )
    }
  }
}
