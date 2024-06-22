package io.mkobit.git.model

sealed interface Section {
  val name: String
  val options: Map<String, Any>

  fun asText(): String = convertSectionToText(this, null)
}

data class UserDefinedSection(
  override val name: String,
  override val options: Map<String, Any>,
) : Section

private fun convertSectionToText(section: Section, subsectionName: String?): String = buildString {
  append('[')
  append(section.name)
  if (subsectionName != null) {
    append(" ")
    append('"')
    append(subsectionName)
    append('"')
  }
  append(']')
  section.options.forEach { (k, v) ->
    appendLine()
    append(" ".repeat(4)) // 4x spaces
    append("$k = $v")
  }
}

fun Section.withName(subsectionName: String) = NamedSection(this, subsectionName)

data class NamedSection(val section: Section, val subsectionName: String) : Section by section {
  override fun asText(): String = convertSectionToText(section, subsectionName)
}

fun Collection<Section>.asText(): String =
  joinToString(separator = "\n", postfix = "\n") { it.asText() }
