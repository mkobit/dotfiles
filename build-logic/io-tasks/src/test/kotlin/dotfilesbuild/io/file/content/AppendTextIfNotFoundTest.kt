package dotfilesbuild.io.file.content

import org.junit.jupiter.api.Test
import strikt.api.expectThat
import strikt.assertions.endsWith
import strikt.assertions.isEqualTo
import strikt.assertions.startsWith
import testsupport.strikt.a
import testsupport.strikt.b
import testsupport.strikt.isLeft
import testsupport.strikt.isRight

internal class AppendTextIfNotFoundTest {
  companion object {
    private const val text =
      """hello
there
my
sweetest
friend"""

    private const val singleLine = "single line of text"
    private const val multiLine =
      """multi
line
text"""
  }

  @Test
  internal fun `appends single line of text if it is not present`() {
    val editAction = AppendTextIfNotFound({ singleLine })
    val either = editAction.applyTo(text)
    expectThat(either)
      .isRight()
      .b
      .startsWith(text)
      .endsWith(singleLine)
  }

  @Test
  internal fun `appends multi-line text if it is not present`() {
    val editAction = AppendTextIfNotFound({ multiLine })
    val either = editAction.applyTo(text)
    expectThat(either)
      .isRight()
      .b
      .startsWith(text)
      .endsWith(multiLine)
  }

  @Test
  internal fun `does not append single line of text if it is present`() {
    val editAction = AppendTextIfNotFound({ singleLine })
    val either = editAction.applyTo(singleLine)
    expectThat(either)
      .isLeft()
      .a
      .isEqualTo(singleLine)
  }

  @Test
  internal fun `does not append multi-line text if it is present`() {
    val editAction = AppendTextIfNotFound({ multiLine })
    val either = editAction.applyTo(multiLine)
    expectThat(either)
      .isLeft()
      .a
      .isEqualTo(multiLine)
  }
}
