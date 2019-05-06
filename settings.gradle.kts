rootProject.name = "dotfiles"

include("chrome-debug-protocol")
include("chrome-debug-protocol-generator")
include("contest-entry")
include("kotlin-script-experiment")
include("java-platform")
include("sidekick-service")

fun String.toKebabCase(): String = split("-").toList().let {
  val suffix = it
    .drop(1)
    .joinToString("") { part ->
      "${part[0].toUpperCase()}${part.substring(1)}"
    }
  "${it.first()}$suffix"
}

rootProject.children.forEach { project ->
  val replacedName = project.name.toKebabCase()
  project.projectDir = file("subprojects/${project.name}")
  project.buildFileName = "$replacedName.gradle.kts"
}

apply(from = file("gradle/buildCache.settings.gradle.kts"))
