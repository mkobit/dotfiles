rootProject.name = "dotfiles"

fun String.toKebabCase(): String = split("-").toList().let {
  val suffix = it
    .drop(1)
    .joinToString("") { part ->
      "${part[0].toUpperCase()}${part.substring(1)}"
    }
  "${it.first()}$suffix"
}

fun includeExperimental(vararg names: String) {
  include(*names)
  names.forEach { name ->
    project(":$name").apply {
      projectDir = file("subprojects/experimental/$name")
    }
  }
}

includeExperimental(
  "chrome-debug-protocol",
  "chrome-debug-protocol-generator",
  "contest-entry",
  "java-platform",
  "kotlin-script-experiment",
  "sidekick-service"
)

rootProject.children.forEach { project ->
  project.buildFileName = "${project.name.toKebabCase()}.gradle.kts"
}

apply(from = file("gradle/buildCache.settings.gradle.kts"))
