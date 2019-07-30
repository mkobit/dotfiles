package dotfilesbuild.kotlin

import dotfilesbuild.dependencies.defaultDotfilesRepositories
import org.gradle.kotlin.dsl.withType
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  java
  kotlin("jvm")
}

repositories.defaultDotfilesRepositories()

java {
  sourceCompatibility = JavaVersion.VERSION_11
}

tasks {
  withType<KotlinCompile>().configureEach {
    kotlinOptions {
      jvmTarget = "11"
      freeCompilerArgs += listOf("-progressive")
    }
  }
}

dependencies {
  api(kotlin("stdlib"))
  api(kotlin("stdlib-jdk8"))
}
