package dotfilesbuild.io.file.content

import org.junit.jupiter.api.Test
import strikt.api.expectThat
import strikt.assertions.isEqualTo
import testsupport.strikt.a
import testsupport.strikt.b
import testsupport.strikt.isLeft
import testsupport.strikt.isRight

internal class SetContentTest {

  companion object {
    private const val text = "text"
  }
  @Test
  internal fun `text is updated and right when it is changed`() {
    val editAction = SetContent { text }

    val either = editAction.applyTo("different")
    expectThat(either)
      .isRight()
      .b
      .isEqualTo(text)
  }

  @Test
  internal fun `text is left when it is unchanged`() {
    val editAction = SetContent { text }

    val either = editAction.applyTo(text)
    expectThat(either)
      .isLeft()
      .a
      .isEqualTo(text)
  }
}
