package dotfilesbuild.io.file.content

import org.junit.jupiter.api.Test
import strikt.api.expectThat
import testsupport.jupiter.NotImplementedYet
import testsupport.strikt.leftWithValue
import testsupport.strikt.rightWithValue

internal class SearchTextReplaceLineTest {

  @Test
  internal fun `matching line is replaced`() {
    val text = "pizza # lunch"
    val action = SearchTextReplaceLine(Regex(".* # lunch")) { text }
    val result = action.applyTo("sandwich # lunch")
    expectThat(result)
        .rightWithValue(text)
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
        .rightWithValue("""
          $text
          $text
          $text
        """.trimIndent())
  }

  @Test
  internal fun `unmatched line is not replaced`() {
    val originalText = "sandwich # lunch".trimIndent()
    val action = SearchTextReplaceLine(Regex(".* # dinner")) { "pizza # dinner" }
    val result = action.applyTo(originalText)
    expectThat(result)
        .leftWithValue(originalText)
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
        .leftWithValue(originalText)
  }
}
