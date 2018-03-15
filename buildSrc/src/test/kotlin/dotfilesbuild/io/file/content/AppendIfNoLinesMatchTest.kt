package dotfilesbuild.io.file.content

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import testsupport.assertThat
internal class AppendIfNoLinesMatchTest {

  companion object {
    private val regex = Regex("^a|b$")
    private val content = { "content" }
  }

  @Test
  internal fun `text is not appended when a line does not match`() {
    val original = "a"
    val editAction = AppendIfNoLinesMatch(regex, content)
    val either = editAction.applyTo(original)
    assertThat(either)
        .isLeftSatisfying {
          assertThat(it)
              .isEqualTo(original)
        }
  }

  @Test
  internal fun `text is not appended when last line matches`() {
    val original = """
      c
      d
      a
    """.trimIndent() + System.lineSeparator()
    val editAction = AppendIfNoLinesMatch(regex, content)
    val either = editAction.applyTo(original)
    assertThat(either)
        .isLeftSatisfying {
          assertThat(it)
              .isEqualTo(original)
        }
  }

  @Test
  internal fun `text is appended when a match is found`() {
    val editAction = AppendIfNoLinesMatch(regex, content)
    val either = editAction.applyTo("c")
    assertThat(either)
        .isRightSatisfying {
          assertThat(it)
              .isEqualTo("""
                c
                ${content()}
              """.trimIndent())
        }
  }
}
