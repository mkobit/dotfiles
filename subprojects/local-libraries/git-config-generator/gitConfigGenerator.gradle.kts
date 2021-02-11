import dotfilesbuild.dependencies.useDotfilesDependencyRecommendations

plugins {
  `java-library`
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.library
}

group = "io.mkobit.git.generator"

configurations.all {
  useDotfilesDependencyRecommendations()
}

dependencies {
  api(kotlin("stdlib"))
  api(kotlin("stdlib-jdk8"))
}
