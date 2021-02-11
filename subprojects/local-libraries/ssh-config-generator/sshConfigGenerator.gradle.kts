import dotfilesbuild.dependencies.useDotfilesDependencyRecommendations

plugins {
  `java-library`
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.library
}

group = "io.mkobit.ssh.config"

configurations.all {
  useDotfilesDependencyRecommendations()
}

dependencies {
  api(kotlin("stdlib"))
  api(kotlin("stdlib-jdk8"))
}
