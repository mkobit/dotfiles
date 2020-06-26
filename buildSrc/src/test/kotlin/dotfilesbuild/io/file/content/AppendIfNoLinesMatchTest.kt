package dotfilesbuild.io.file.content

import org.junit.jupiter.api.Test
import strikt.api.expectThat
import strikt.assertions.isEqualTo
import testsupport.strikt.a
import testsupport.strikt.b
import testsupport.strikt.isLeft
import testsupport.strikt.isRight

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
    expectThat(either)
      .isLeft()
      .a
      .isEqualTo(original)
  }

  @Test
  internal fun `text is not appended when last line matches`() {
    val original =
      """
      c
      d
      a
      """.trimIndent() + System.lineSeparator()
    val editAction = AppendIfNoLinesMatch(regex, content)
    val either = editAction.applyTo(original)
    expectThat(either)
      .isLeft()
      .a
      .isEqualTo(original)
  }

  @Test
  internal fun `text is appended when a match is found`() {
    val editAction = AppendIfNoLinesMatch(regex, content)
    val either = editAction.applyTo("c")
    expectThat(either)
      .isRight()
      .b
      .isEqualTo(
        """
                c
                ${content()}
        """.trimIndent()
      )
  }
}
