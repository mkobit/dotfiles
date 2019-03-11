package com.mkobit.cdp.pdl

import java.nio.file.Path


private val domainRegex = Regex("^(experimental )?(deprecated )?domain (.*)")
private val domainDependencyRegex = Regex("^ {2}depends on ([^\\s]+)")
private val typeRegex = Regex("^ {2}(experimental )?(deprecated )?type (.*) extends (array of )?([^\\s]+)")
private val commandAndEventRegex = Regex("^ {2}(experimental )?(deprecated )?(command|event) (.*)")
private val someRegex = Regex("^ {6}(experimental )?(deprecated )?(optional )?(array of )?([^\\s]+) ([^\\s]+)")
private val paramatersReturnsAndPropertiesRegex = Regex("^ {4}(parameters|returns|properties)")
private val enumRegex = Regex("^ {4}enum")
private val versionRegex = Regex("^version")
private val majorVersionRegex = Regex("^ {2}major (\\d+)")
private val minorVersionRegex = Regex("^ {2}minor (\\d+)")

fun parse(path: Path) {
  val lines = path.toFile().readLines()
  // read comment header
  val (_, headerCommentOffset) = parseSection(lines, 0)
  val (version, versionOffset) = parseSection(lines, headerCommentOffset)


  TODO()
}

private fun parseSection(lines: List<String>, offset: Int): Pair<PdlSection, Int> {
  val firstLine = lines[offset]
  val trimmedFirstLine = firstLine.trim()
  return when {
    "domain" in firstLine -> parseDomainSection(lines, offset)
    trimmedFirstLine.startsWith("# ") -> parseCommentSection(lines, offset)
    "type" in firstLine -> parseTypeSection(lines, offset)
    "command" in firstLine -> parseCommandSection(lines, offset)
    "event" in firstLine -> parseEventSection(lines, offset)
    else -> throw UnsupportedOperationException("Unparseable section with first line '$firstLine'")
  }
}

private fun parseDomainSection(lines: List<String>, offset: Int): Pair<PdlSection, Int> {
  TODO()
}

private fun parseTypeSection(lines: List<String>, offset: Int): Pair<PdlSection, Int> {
  TODO()
}

private fun parseCommandSection(lines: List<String>, offset: Int): Pair<PdlSection, Int> {
  TODO()
}

private fun parseEventSection(lines: List<String>, offset: Int): Pair<PdlSection, Int> {
  TODO()
}

private fun parseCommentSection(lines: List<String>, offset: Int): Pair<PdlSection, Int> {
  check(lines[offset].trim().startsWith("# ")) { "First line must start with a #" }
  val commentLines = lines.asSequence()
      .drop(offset)
      .map { it.trim() }
      .takeWhile { it.startsWith("# ") }
      .map { it.substring(2) } // remove the '# ' beginning
      .toList()

  return PdlSection.CommentSection(commentLines.joinToString(separator = " ")) to (offset + commentLines.size)
}

private sealed class PdlSection {
  data class CommentSection(val comment: String) : PdlSection()
  data class DomainSection(
      val name: String,
      val comment: CommentSection?,
      val dependsOnReferences: List<String>
  ) : PdlSection()
  data class TypeSection(val name: String) : PdlSection()
  data class CommandSection(val paramaters: List<CommandParamater>) {
    class CommandParamater
  }
}


data class Definitions(
    val version: Version,
    val domains: Set<Domain>
)

data class Version(val major: String, val minor: String)

data class Domain(
    val name: String,
    val dependsOn: Set<Domain>,
    val types: Set<Type>
)

data class Type(
    val name: String
)
