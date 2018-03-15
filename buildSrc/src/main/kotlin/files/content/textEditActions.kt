package files.content

import arrow.core.Either
import java.util.regex.Pattern

private val newline: Regex = Regex(System.lineSeparator())

interface TextEditAction {
  /**
   * @return [Either.Right] when a change was applied, otherwise [Either.Left]
   */
  fun applyTo(text: String): Either<String, String>
}

class SetContent(
    private val content: () -> CharSequence
) : TextEditAction {
  override fun applyTo(text: String): Either<String, String> {
    val newText = content().toString()
    return if (text == newText) {
      Either.left(text)
    } else {
      Either.right(newText)
    }
  }
}

class AppendIfNoLinesMatch(
    private val regex: Regex,
    private val content: () -> CharSequence
) : TextEditAction {

  constructor(pattern: Pattern, content: () -> CharSequence): this(pattern.toRegex(), content)

  override fun applyTo(text: String): Either<String, String> {
    val textToInsert = content().toString()
    val noneMatch = text.split(newline).none { it.matches(regex) }
    return if (noneMatch) {
      val separator = if (text.endsWith(System.lineSeparator())) {
        ""
      } else {
        System.lineSeparator()
      }
      Either.right(text + separator + textToInsert)
    } else {
      Either.left(text)
    }
  }
}

class AppendTextIfNotFound(
    private val content: () -> CharSequence
) : TextEditAction {
  override fun applyTo(text: String): Either<String, String> {
    val textToInsert = content()
    return if (!text.contains(textToInsert)) {
      val separator = if (text.endsWith(System.lineSeparator())) {
        ""
      } else {
        System.lineSeparator()
      }
      Either.right(text + separator + textToInsert)
    } else {
      Either.left(text)
    }
  }
}

class SearchFileDeleteLine(
    private val regex: Regex
) : TextEditAction {

  constructor(pattern: Pattern): this(pattern.toRegex())

  override fun applyTo(text: String): Either<String, String> {
    val newText = text.split(newline)
        .filter { !it.matches(regex) }
        .joinToString(System.lineSeparator())
    return if (newText != text) {
      Either.right(newText)
    } else {
      Either.left(text)
    }
  }
}
