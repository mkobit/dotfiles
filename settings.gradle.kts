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

"shell".let { p ->
  include("$p:aggregator")
  include("$p:external-configuration")
  include("$p:diff-highlight")
  include("$p:git")
  include("$p:ssh")
  include("$p:take-note")
  include("$p:tmux")
  include("$p:vim")
}

"local-libraries".let { p ->
  include("$p:pico-cli-utils")
  include("$p:git-config-generator")
  include("$p:ssh-config-generator")
}

"programs".let { p ->
  include("$p:jq")
  include("$p:keepass")
  include("$p:kubectl")
}

"experimental".let { p ->
  include("$p:chrome-debug-protocol")
  include("$p:chrome-debug-protocol-generator")
  include("$p:kotlin-script-experiment")
  include("$p:sidekick-service")
}

fun configureSubproject(projectDescriptor: ProjectDescriptor) {
  projectDescriptor.buildFileName = "${projectDescriptor.name.toKebabCase()}.gradle.kts"
  projectDescriptor.projectDir =
    file("subprojects/${projectDescriptor.path.replace(":", "/")}")
  projectDescriptor.children.forEach { configureSubproject(it) }
}

rootProject.children.forEach { project -> configureSubproject(project) }

apply(from = file("gradle/buildCache.settings.gradle.kts"))
