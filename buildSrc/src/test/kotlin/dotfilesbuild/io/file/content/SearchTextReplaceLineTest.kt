package dotfilesbuild.io.file.content

import org.junit.jupiter.api.Test
import strikt.api.expectThat
import strikt.assertions.isEqualTo
import testsupport.jupiter.NotImplementedYet
import testsupport.strikt.a
import testsupport.strikt.b
import testsupport.strikt.isLeft
import testsupport.strikt.isRight

internal class SearchTextReplaceLineTest {

  @Test
  internal fun `matching line is replaced`() {
    val text = "pizza # lunch"
    val action = SearchTextReplaceLine(Regex(".* # lunch")) { text }
    val result = action.applyTo("sandwich # lunch")
    expectThat(result)
      .isRight()
      .b
      .isEqualTo(text)
  }

  @NotImplementedYet
  @Test
  internal fun `replaces specified quantity of matched lines`() {
    TODO()
  }

  @Test
  internal fun `all multiple matching lines are replaced`() {
    val text = "pizza # lunch"
    val action = SearchTextReplaceLine(Regex(".* # lunch")) { text }
    val result = action.applyTo("""
        sandwich # lunch
        salad # lunch
        pasta # lunch
      """.trimIndent()
    )
    expectThat(result)
      .isRight()
      .b
      .isEqualTo(
          """
            $text
            $text
            $text
          """.trimIndent()
      )
  }

  @Test
  internal fun `unmatched line is not replaced`() {
    val originalText = "sandwich # lunch".trimIndent()
    val action = SearchTextReplaceLine(Regex(".* # dinner")) { "pizza # dinner" }
    val result = action.applyTo(originalText)
    expectThat(result)
      .isLeft()
      .a
      .isEqualTo(originalText)
  }

  @Test
  internal fun `unmatched lines are not replaced`() {
    val originalText = """
      sandwich # lunch
      salad # lunch
      pasta # lunch
    """.trimIndent()
    val action = SearchTextReplaceLine(Regex(".* # dinner")) { "pizza # dinner" }
    val result = action.applyTo(originalText)
    expectThat(result)
      .isLeft()
      .a
      .isEqualTo(originalText)
  }
}
