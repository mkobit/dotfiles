plugins {
  id("com.gradle.enterprise") version "3.3.4"
}

rootProject.name = "dotfiles"

fun String.toKebabCase(): String = split("-").toList().let {
  val suffix = it
    .drop(1)
    .joinToString("") { part ->
      "${part[0].toUpperCase()}${part.substring(1)}"
    }
  "${it.first()}$suffix"
}

"shell".let {
  include("$it:aggregator")
  include("$it:external-configuration")
  include("$it:diff-highlight")
  include("$it:git")
  include("$it:ssh")
  include("$it:take-note")
  include("$it:tmux")
  include("$it:vim")
}

"local-libraries".let {
  include("$it:pico-cli-utils")
  include("$it:git-config-generator")
  include("$it:ssh-config-generator")
}

"programs".let {
  include("$it:jq")
  include("$it:keepass")
  include("$it:kubectl")
}

"experimental".let {
  include("$it:chrome-debug-protocol")
  include("$it:chrome-debug-protocol-generator")
  include("$it:kotlin-script-experiment")
  include("$it:sidekick-service")
}

fun configureSubproject(projectDescriptor: ProjectDescriptor) {
  projectDescriptor.buildFileName = "${projectDescriptor.name.toKebabCase()}.gradle.kts"
  projectDescriptor.projectDir =
    file("subprojects/${projectDescriptor.path.replace(":", "/")}")
  projectDescriptor.children.forEach { configureSubproject(it) }
}

rootProject.children.forEach { project -> configureSubproject(project) }

apply(from = file("gradle/buildCache.settings.gradle.kts"))
