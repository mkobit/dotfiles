plugins {
  id("org.jlleitschuh.gradle.ktlint")
  id("dotfilesbuild.kotlin.library")
  application
}

val bin by configurations.creating {
  isCanBeConsumed = true
  isCanBeResolved = false
  attributes {
    attribute(Usage.USAGE_ATTRIBUTE, objects.named(Usage::class, "bin"))
  }
}

dependencies {
  implementation(libs.picocli.cli)

  implementation(kotlin("stdlib-jdk8"))
  implementation(libs.coroutines.core)
  implementation(libs.coroutines.jdk8)

  implementation(libs.kotlinLogging)
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
