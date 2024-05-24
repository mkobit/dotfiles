@file:OptIn(ExperimentalKotest::class)

package io.mkobit.git.model

import io.kotest.common.ExperimentalKotest
import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.collections.shouldContainExactly
import io.mkobit.testing.kotest.condition.NotImplemented
import kotlinx.io.files.Path

internal class GitConfigTest : FunSpec({
  test("named section as text") {
    val subject = NamedSection(
      User(
        userName = "mike.kobit",
        email = "mike.kobit@example.com"
      ),
      "myusersubsection"
    )
    subject.asText().lines()
      .shouldContainExactly(
        """[user "myusersubsection"]""",
        "    email = mike.kobit@example.com",
        "    name = mike.kobit",
      )
  }

  test("alias section as text") {
    val subject = Alias(
      mapOf(
        "aa" to "add --all",
        "amend" to "commit --amend",
        "soft-reset" to "!git reset --soft HEAD~1 && git reset HEAD .",
        "wip" to "commit -am 'WIP'"
      )
    )

    subject.asText().lines()
      .shouldContainExactly(
        "[alias]",
        "    aa = add --all",
        "    amend = commit --amend",
        "    soft-reset = !git reset --soft HEAD~1 && git reset HEAD .",
        "    wip = commit -am 'WIP'",
      )
  }

//  context("IncludeTest") {
    test("include path") {
      val subject = Include(Path("~/.my_git_config"))
      subject.asText().lines()
        .shouldContainExactly(
          "[include]",
          "    path = ~/.my_git_config"
        )
    }

    test("includeIf gitdir") {
      val subject = Include(Path("~/.my_git_config")).ifGitDir(Path("/path/to/group"))

      subject.asText().lines()
        .shouldContainExactly(
          "[includeIf \"gitdir:/path/to/group\"]",
          "    path = ~/.my_git_config"
        )
    }

    test("includeIf onbranch") {
      val subject = Include(Path("~/.my_git_config")).ifOnBranch("mybranch/**")

      subject.asText().lines()
        .shouldContainExactly(
          "[includeIf \"onbranch:mybranch/**\"]",
          "    path = ~/.my_git_config"
        )
    }
//  }

//  context("PathEscapeTest").config(enabledOrReasonIf = NotImplemented) {
    test("escape include path with double quotes").config(enabledOrReasonIf = NotImplemented) {
      val subject = Include(Path("""~/"My Workspace"/\"Work\"/superteam"""))
      subject.asText().lines()
        .shouldContainExactly(
          """    path = "~/\"My Workspace\"/\"Work\"/superteam""""
        )
    }
//  }

  test("section collection as text") {
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

    sections.asText().lines()
      .shouldContainExactly(
        "[alias]",
        "    a = 1",
        "[alias \"subsectionName\"]",
        "    b = 2",
        "[include]",
        "    path = ~/.my_git_config",
        ""
      )
  }
})
