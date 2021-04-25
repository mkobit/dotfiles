plugins {
  `java-library`
  // id("org.jlleitschuh.gradle.ktlint")
  id("dotfilesbuild.kotlin.library")
}

dependencies {
  api(libs.picocli.cli)
  api(kotlin("stdlib"))
  api(kotlin("stdlib-jdk8"))
}
