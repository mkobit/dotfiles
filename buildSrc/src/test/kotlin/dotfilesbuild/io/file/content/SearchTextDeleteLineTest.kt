package dotfilesbuild.io.file.content

import org.junit.jupiter.api.Test
import strikt.api.expectThat
import strikt.assertions.containsExactly
import strikt.assertions.isBlank
import strikt.assertions.isEqualTo
import testsupport.strikt.a
import testsupport.strikt.b
import testsupport.strikt.isLeft
import testsupport.strikt.isRight

internal class SearchTextDeleteLineTest {

  companion object {
    private val regex = Regex("^a|b$")
  }

  @Test
  internal fun `text is removed when a match is found`() {
    val editAction = SearchTextDeleteLine(regex)
    val either = editAction.applyTo("a")
    expectThat(either)
      .isRight()
      .b
      .isBlank()
  }

  @Test
  internal fun `all matches are removed`() {
    val editAction = SearchTextDeleteLine(regex)
    val either = editAction.applyTo(
      """
        a
        b
        c
        a
        b
        c
      """.trimIndent()
    )
    expectThat(either)
      .isRight()
      .b
      .get { split("\n") }.and {
        get { count() }.isEqualTo(2)
        containsExactly("c", "c")
      }
  }

  @Test
  internal fun `text is unchanged when a match is not found`() {
    val editAction = SearchTextDeleteLine(regex)
    val either = editAction.applyTo("c")
    expectThat(either)
      .isLeft()
      .a
      .isEqualTo("c")
  }
}
