plugins {
  `java-library`
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.library
}

dependencies {
  api(libs.picocli.cli)
  api(kotlin("stdlib"))
  api(kotlin("stdlib-jdk8"))
}
