package files.content

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import testsupport.assertThat

internal class AppendTextIfNotFoundTest {
  companion object {
    private const val text = """hello
there
my
sweetest
friend"""

    private const val singleLine = "single line of text"
    private const val multiLine = """multi
line
text"""
  }
  @Test
  internal fun `appends single line of text if it is not present`() {
    val editAction = AppendTextIfNotFound({ singleLine })
    val either = editAction.applyTo(text)
    assertThat(either)
        .isRightSatisfying {
          assertThat(it)
              .startsWith(text)
              .endsWith(singleLine)
        }
  }

  @Test
  internal fun `appends multi-line text if it is not present`() {
    val editAction = AppendTextIfNotFound({ multiLine })
    val either = editAction.applyTo(text)
    assertThat(either)
        .isRightSatisfying {
          assertThat(it)
              .startsWith(text)
              .endsWith(multiLine)
        }
  }

  @Test
  internal fun `does not append single line of text if it is present`() {
    val editAction = AppendTextIfNotFound({ singleLine })
    val either = editAction.applyTo(singleLine)
    assertThat(either)
        .isLeftSatisfying {
          assertThat(it).isEqualTo(singleLine)
        }
  }

  @Test
  internal fun `does not append multi-line text if it is present`() {
    val editAction = AppendTextIfNotFound({ multiLine })
    val either = editAction.applyTo(multiLine)
    assertThat(either)
        .isLeftSatisfying {
          assertThat(it).isEqualTo(multiLine)
        }
  }
}
