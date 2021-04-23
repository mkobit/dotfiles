plugins {
  `java-library`
  id("org.jlleitschuh.gradle.ktlint")
  id("dotfilesbuild.kotlin.library")
}

group = "io.mkobit.strikt.scripting"

dependencies {
  api(testLibs.strikt.core)
  api(kotlin("scripting-common"))
  api(kotlin("stdlib"))
  api(kotlin("stdlib-jdk8"))
}
