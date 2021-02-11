package io.mkobit.git.config

import org.junit.jupiter.api.Disabled
import org.junit.jupiter.api.Nested
import org.junit.jupiter.api.Test
import strikt.api.expectThat
import strikt.assertions.contains
import strikt.assertions.containsExactly
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.Path

@ExperimentalPathApi
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

  @Disabled("not implemented yet")
  @Nested
  internal inner class PathEscapeTest {
    @Test
    internal fun `include path with double quotes`() {
      val subject = Include(Path("""~/"My Workspace"/\"Work\"/superteam"""))
      expectThat(subject.asText().lines())
        .contains(
          """    path = "~/\"My Workspace\"/\"Work\"/superteam""""
        )
    }
  }

  @Test
  internal fun `section collection as text`() {
    val sections = listOf(
      Alias(
        mapOf(
          "a" to "1"
        )
      ),
      NamedSection(
        Alias(
          mapOf(
            "b" to "2"
          )
        ),
        "subsectionName"
      ),
      Include(Path("~/.my_git_config"))
    )

    expectThat(sections.asText().lines())
      .containsExactly(
        "[alias]",
        "    a = 1",
        "[alias \"subsectionName\"]",
        "    b = 2",
        "[include]",
        "    path = ~/.my_git_config",
        ""
      )
  }
}
