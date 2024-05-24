pluginManagement {
  includeBuild("../build-logic-settings")
}

plugins {
  id("dotfilesbuild.version-catalog")
}

rootProject.name = "build-logic"

dependencyResolutionManagement {
  repositories {
    mavenCentral()
    gradlePluginPortal()
  }
}

apply(from = file("../gradle/shared.settings.gradle.kts"))

enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")

include("dotfiles-lifecycle")
include("extension-utilities")
include("hocon-config")
include("intellij-program")
include("io-tasks")
include("jq-program")
include("keepass-program")
include("kotlin-plugins")
include("ktlint-convention")
include("kubectl-program")
