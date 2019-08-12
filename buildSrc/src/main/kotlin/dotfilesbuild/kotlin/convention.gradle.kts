package dotfilesbuild.kotlin

import dotfilesbuild.dependencies.defaultDotfilesRepositories
import dotfilesbuild.dependencies.junitTestImplementationArtifacts
import dotfilesbuild.dependencies.junitTestRuntimeOnlyArtifacts
import dotfilesbuild.dependencies.strikt
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

  withType<Test>().configureEach {
    useJUnitPlatform()
  }
}

dependencies {
  implementation(kotlin("stdlib"))
  implementation(kotlin("stdlib-jdk8"))

  testImplementation("dev.minutest:minutest:1.7.0")
  testImplementation(strikt("core"))
  junitTestImplementationArtifacts.forEach {
    testImplementation(it)
  }
  junitTestRuntimeOnlyArtifacts.forEach {
    testRuntimeOnly(it)
  }
}
