package dotfilesbuild.io.file.content

import org.junit.jupiter.api.Test
import strikt.api.expectThat
import strikt.assertions.isEqualTo
import testsupport.strikt.isLeft
import testsupport.strikt.isRight

internal class ReplaceTextTest {

  @Test
  internal fun `when single line text is matched then it is replaced`() {
    val text = "salad # lunch"
    val replacementText = "pizza # lunch"
    val replaceText = ReplaceText(Regex(".* # lunch"), false) { replacementText }
    val result = replaceText.applyTo(text)

    expectThat(result)
      .isRight()
      .isEqualTo(replacementText)
  }

  @Test
  internal fun `when single line text is matched but it results in the same text then it is not replaced`() {
    val text = "salad # lunch"
    val replaceText = ReplaceText(Regex(".* # lunch"), false) { text }
    val result = replaceText.applyTo(text)

    expectThat(result)
      .isLeft()
      .isEqualTo(text)
  }

  @Test
  internal fun `when single line text is not-matched and append-if-not-present is enabled then it is appended to the end`() {
    val text = "salad # lunch"
    val replacementText = "pizza # dinner"
    val replaceText = ReplaceText(Regex(".* # dinner"), true) { replacementText }
    val result = replaceText.applyTo(text)

    expectThat(result)
      .isRight()
      .isEqualTo(
        """
          $text
          $replacementText
        """.trimIndent()
      )
  }

  @Test
  internal fun `when single line text is not-matched and append-if-not-present is disabled then it is not appended to the end`() {
    val text = "salad # lunch"
    val replacementText = "pizza # dinner"
    val replaceText = ReplaceText(Regex(".* # dinner"), false) { replacementText }
    val result = replaceText.applyTo(text)

    expectThat(result)
      .isLeft()
      .isEqualTo(text)
  }
}
