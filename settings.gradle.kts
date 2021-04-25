pluginManagement {
  includeBuild("build-logic-settings")
}

plugins {
  id("com.gradle.enterprise") version "3.6.1"
  id("dotfilesbuild.version-catalog")
}

rootProject.name = "dotfiles"

dependencyResolutionManagement {
  repositories {
    mavenCentral()
    jcenter()
  }
}

includeBuild("build-logic")

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
    include("$git:config-generator")
    include("$git:script-definition")
  }
  "$it:ssh".let { ssh ->
    include("$ssh:config-generator")
    include("$ssh:script-definition")
    include("$ssh:script-host")
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
  include("$it:kotlin-script-experiment")
  include("$it:sidekick-service")
}

rootProject.children.forEach { project -> configureSubproject(project) }

apply(from = file("gradle/buildCache.settings.gradle.kts"))

enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")
enableFeaturePreview("VERSION_CATALOGS")

fun configureSubproject(projectDescriptor: ProjectDescriptor) {
  projectDescriptor.projectDir =
    file("subprojects/${projectDescriptor.path.replace(":", "/")}")
  projectDescriptor.children.forEach { configureSubproject(it) }
}
