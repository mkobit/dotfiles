package io.mkobit.git.config

private fun convertSectionToText(section: Section, subsectionName: String?): String =
  "[${section.name}${subsectionName?.let { sn -> " \"$sn\"" } ?: ""}]" +
    if (section.options.isNotEmpty()) {
      section.options.entries.joinToString(
        separator = System.lineSeparator(),
        prefix = System.lineSeparator(),
      ) {
        "${it.key} = ${it.value}".prependIndent(" ".repeat(4))
      }
    } else {
      System.lineSeparator()
    }

fun Section.asText(): String = convertSectionToText(this, null)

fun NamedSection.asText(): String = convertSectionToText(section, name)
