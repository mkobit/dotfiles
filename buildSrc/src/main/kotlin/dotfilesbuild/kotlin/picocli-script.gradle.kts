package dotfilesbuild.kotlin

import dotfilesbuild.dependencies.defaultDotfilesRepositories
import dotfilesbuild.dependencies.junitTestImplementationArtifacts
import dotfilesbuild.dependencies.junitTestRuntimeOnlyArtifacts
import dotfilesbuild.dependencies.minutest
import dotfilesbuild.dependencies.hocon
import dotfilesbuild.dependencies.picoCli
import dotfilesbuild.dependencies.strikt
import org.gradle.kotlin.dsl.withType
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  application
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

  (run) {
    mainClass.set(provider { "${project.group}.${project.name}.Main" })
  }
}

dependencies {
  implementation(picoCli)
  implementation(hocon)
  implementation(kotlin("stdlib"))
  implementation(kotlin("stdlib-jdk8"))

  testImplementation(strikt("core"))
  testImplementation(minutest("minutest"))
  junitTestImplementationArtifacts.forEach {
    testImplementation(it)
  }
  junitTestRuntimeOnlyArtifacts.forEach {
    testRuntimeOnly(it)
  }
}
