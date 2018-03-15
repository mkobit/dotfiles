package files.content

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import testsupport.assertThat

internal class SetContentTest {

  companion object {
    private const val text = "text"
  }
  @Test
  internal fun `text is updated and right when it is changed`() {
    val editAction = SetContent({ text })

    val either = editAction.applyTo("different")
    assertThat(either)
        .isRightSatisfying {
          assertThat(it)
              .isEqualTo(text)
        }
  }

  @Test
  internal fun `text is left when it is unchanged`() {
    val editAction = SetContent({ text })

    val either = editAction.applyTo(text)
    assertThat(either)
        .isLeftSatisfying {
          assertThat(it)
              .isEqualTo(text)
        }
  }
}
