package io.mkobit.git.config

import org.junit.jupiter.api.Test
import strikt.api.expectThat
import strikt.assertions.containsExactly

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
}