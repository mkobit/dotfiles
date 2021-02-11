import dotfilesbuild.dependencies.kotlinLogging
import dotfilesbuild.dependencies.kotlinxCoroutines
import dotfilesbuild.dependencies.picoCli
import dotfilesbuild.dependencies.useDotfilesDependencyRecommendations

plugins {
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.library
  application
}

val bin by configurations.creating {
  isCanBeConsumed = true
  isCanBeResolved = false
  attributes {
    attribute(Usage.USAGE_ATTRIBUTE, objects.named(Usage::class, "bin"))
  }
}

configurations.all {
  useDotfilesDependencyRecommendations()
}

dependencies {
  implementation(picoCli)

  implementation(kotlin("stdlib-jdk8"))
  implementation(kotlinxCoroutines("core"))
  implementation(kotlinxCoroutines("jdk8"))

  implementation(kotlinLogging)
}

application {
  mainClass.set("dotfiles.mkobit.cli.note.Main")
}

tasks {
  distZip {
    enabled = false
  }

  distTar {
    enabled = false
  }
}

bin.outgoing.artifact(tasks.installDist.map { it.destinationDir }.map { it.resolve("bin") })
