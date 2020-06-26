import dotfilesbuild.dependencies.picoCli
import dotfilesbuild.dependencies.useDotfilesDependencyRecommendations

plugins {
  `java-library`
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.convention
}

ktlint {
  version.set("0.37.2")
}

configurations.all {
  useDotfilesDependencyRecommendations()
}

dependencies {
  api(picoCli)
  api(kotlin("stdlib"))
  api(kotlin("stdlib-jdk8"))
}
