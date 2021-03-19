plugins {
  id("com.gradle.enterprise") version "3.3.4"
}

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

fun includeGroup(group: String, names: Collection<String>) {
  names.forEach { name ->
    include("$group:$name")
    project(":$group:$name").apply {
      projectDir = subprojectFile(group, name)
    }
  }
}

includeGroup(
  "shell",
  listOf(
    "aggregator",
    "external-configuration",
    "diff-highlight",
    "git",
    "ssh",
    "take-note",
    "tmux",
    "vim"
  )
)

includeGroup(
  "local-libraries",
  listOf(
    "pico-cli-utils",
    "git-config-generator",
    "ssh-config-generator"
  )
)

includeGroup(
  "programs",
  listOf(
    "jq",
    "keepass",
    "kubectl"
  )
)

includeGroup(
  "experimental",
  listOf(
    "chrome-debug-protocol",
    "chrome-debug-protocol-generator",
    "kotlin-script-experiment",
    "sidekick-service"
  )
)

fun configureBuildfiles(projectDescriptor: ProjectDescriptor) {
  projectDescriptor.buildFileName = "${projectDescriptor.name.toKebabCase()}.gradle.kts"
  projectDescriptor.children.forEach { configureBuildfiles(it) }
}

rootProject.children.forEach { project -> configureBuildfiles(project) }

apply(from = file("gradle/buildCache.settings.gradle.kts"))
