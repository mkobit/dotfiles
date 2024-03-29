pluginManagement {
  includeBuild("build-logic-settings")
}

plugins {
  id("dotfilesbuild.version-catalog")
}

includeBuild("build-logic")

rootProject.name = "dotfiles"

dependencyResolutionManagement {
  repositories {
    mavenCentral()
  }
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
  "$it:git".let { git ->
    include("$git:git-config-generator")
    include("$git:git-config-script")
  }
  "$it:ssh".let { ssh ->
    include("$ssh:ssh-config-generator")
    include("$ssh:ssh-config-script")
  }
  "$it:testing".let { testing ->
    include("$testing:strikt-kotlin-scripting")
  }
}

"programs".let {
  include("$it:jq")
  include("$it:keepass")
  include("$it:kubectl")
}

"experimental".let {
  include("$it:chrome-debug-protocol")
  include("$it:chrome-debug-protocol-generator")
  include("$it:sidekick-service")
}

rootProject.children.forEach { project -> configureSubproject(project) }

apply(from = file("gradle/buildCache.settings.gradle.kts"))

enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")

fun configureSubproject(projectDescriptor: ProjectDescriptor) {
  projectDescriptor.projectDir =
    file("subprojects/${projectDescriptor.path.replace(":", "/")}")
  projectDescriptor.children.forEach { configureSubproject(it) }
}
