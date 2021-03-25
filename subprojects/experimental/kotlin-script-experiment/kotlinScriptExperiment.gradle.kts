import dotfilesbuild.dependencies.kotlinLogging
import dotfilesbuild.dependencies.jacksonCore
import dotfilesbuild.dependencies.jacksonModule
import dotfilesbuild.dependencies.useDotfilesDependencyRecommendations

plugins {
  dotfilesbuild.kotlin.library
  id("org.jlleitschuh.gradle.ktlint")
}

configurations.all {
  useDotfilesDependencyRecommendations()
}

dependencies {
  implementation(jacksonCore("core"))
  implementation(jacksonModule("kotlin"))

  implementation(kotlin("compiler-embeddable"))
  implementation(kotlin("stdlib-jdk8"))
  implementation(kotlin("scripting-common"))
  implementation(kotlin("scripting-jvm"))
  implementation(kotlin("scripting-jvm-host"))

  implementation(kotlinLogging)
}
