plugins {
  dotfilesbuild.kotlin.library
  id("org.jlleitschuh.gradle.ktlint")
}

dependencies {
  implementation(libs.jackson.core.core)
  implementation(libs.jackson.module.kotlin)

  implementation(kotlin("compiler-embeddable"))
  implementation(kotlin("stdlib-jdk8"))
  implementation(kotlin("scripting-common"))
  implementation(kotlin("scripting-jvm"))
  implementation(kotlin("scripting-jvm-host"))

  implementation(libs.kotlinLogging)
}
