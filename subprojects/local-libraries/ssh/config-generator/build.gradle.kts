plugins {
  `java-library`
  // id("org.jlleitschuh.gradle.ktlint")
  id("dotfilesbuild.kotlin.library")
}

group = "io.mkobit.ssh.config"

dependencies {
  api(kotlin("stdlib"))
  api(kotlin("stdlib-jdk8"))
}
