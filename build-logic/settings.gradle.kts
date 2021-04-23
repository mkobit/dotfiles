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

//enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")

include("dotfiles-lifecycle")
include("hocon-config")
include("io-tasks")
include("keepass-program")
include("kotlin-library")
include("kotlin-cli-script")
