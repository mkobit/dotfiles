rootProject.name = "dotfiles"

fun subprojectFile(group: String, name: String) = file("subprojects/$group/$name")

fun String.toKebabCase(): String = split("-").toList().let {
  val suffix = it
    .drop(1)
    .joinToString("") { part ->
      "${part[0].toUpperCase()}${part.substring(1)}"
    }
  "${it.first()}$suffix"
}

fun includeGroup(group: String, vararg names: String) {
  include(*names)
  names.forEach { name ->
    project(":$name").apply {
      projectDir = subprojectFile(group, name)
    }
  }
}

fun includeExperimental(vararg names: String) = includeGroup("experimental", *names)
fun includeLocalLibraries(vararg names: String) = includeGroup("local-libraries", *names)
fun includePrograms(vararg names: String) = includeGroup("programs", *names)
fun includeShell(vararg names: String) = includeGroup("shell", *names)

includeShell(
  "aggregator",
  "bin-managed",
  "bin-unmanaged",
  "git",
  "ssh",
  "take-note",
  "tmux",
  "vim"
)

includeLocalLibraries(
  "cli-utils"
)

includePrograms(
  "intellij",
  "keepass",
  "kubectl"
)

includeExperimental(
  "chrome-debug-protocol",
  "chrome-debug-protocol-generator",
  "contest-entry",
  "kotlin-script-experiment",
  "sidekick-service"
)

rootProject.children.forEach { project ->
  project.buildFileName = "${project.name.toKebabCase()}.gradle.kts"
}

apply(from = file("gradle/buildCache.settings.gradle.kts"))
