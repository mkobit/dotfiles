plugins {
  `java-library`
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.library
}

group = "io.mkobit.git.generator"

dependencies {
  api(kotlin("stdlib"))
  api(kotlin("stdlib-jdk8"))
}
