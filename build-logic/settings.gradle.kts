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
    jcenter()
  }
}

apply(from = file("../gradle/buildCache.settings.gradle.kts"))

include("dotfiles-lifecycle")
include("io-tasks")
include("kotlin-library")
include("kotlin-cli-script")
