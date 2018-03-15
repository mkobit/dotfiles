package dotfilesbuild.io.file.content

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import testsupport.assertThat

internal class SearchFileDeleteLineTest {

  companion object {
    private val regex = Regex("^a|b$")
    private val content = { "content" }
  }

  @Test
  internal fun `text is removed when a match is found`() {
    val editAction = SearchFileDeleteLine(regex)
    val either = editAction.applyTo("a")
    assertThat(either)
        .isRightSatisfying {
          assertThat(it)
              .isBlank()
        }
  }

  @Test
  internal fun `all matches are removed`() {
    val editAction = SearchFileDeleteLine(regex)
    val either = editAction.applyTo("""
        a
        b
        c
        a
        b
        c
      """.trimIndent())
    assertThat(either)
        .isRightSatisfying {
          assertThat(it)
              .hasLineCount(2)
              .isEqualToIgnoringNewLines("cc")
        }
  }

  @Test
  internal fun `text is unchanged when a match is not found`() {
    val editAction = SearchFileDeleteLine(regex)
    val either = editAction.applyTo("c")
    assertThat(either)
        .isLeftSatisfying {
          assertThat(it)
              .isEqualTo("c")
        }
  }
}
