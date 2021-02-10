import dotfilesbuild.dependencies.useDotfilesDependencyRecommendations

plugins {
  `java-library`
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.library
}

group = "io.mkobit.ssh.config"

ktlint {
  version.set("0.39.0")
}

configurations.all {
  useDotfilesDependencyRecommendations()
}

dependencies {
  api(kotlin("stdlib"))
  api(kotlin("stdlib-jdk8"))
}
