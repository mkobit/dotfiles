import dotfilesbuild.dependencies.strikt

plugins {
  `java-library`
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.library
}

group = "io.mkobit.strikt.scripting"

dependencies {
  api(strikt("core"))
  api(kotlin("scripting-common"))
  api(kotlin("stdlib"))
  api(kotlin("stdlib-jdk8"))
}
