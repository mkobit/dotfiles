package dotfilesbuild.kotlin

import dotfilesbuild.dependencies.junitTestImplementationArtifacts
import dotfilesbuild.dependencies.junitTestRuntimeOnlyArtifacts
import dotfilesbuild.dependencies.minutest
import dotfilesbuild.dependencies.strikt
import dotfilesbuild.dependencies.useDotfilesDependencyRecommendations
import org.gradle.kotlin.dsl.withType
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  `java-library`
  kotlin("jvm")
}

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

configurations.all {
  useDotfilesDependencyRecommendations()
}

dependencies {
  api(kotlin("stdlib"))
  api(kotlin("stdlib-jdk8"))

  testImplementation(strikt("core"))
  testImplementation(minutest("minutest"))
  junitTestImplementationArtifacts.forEach {
    testImplementation(it)
  }
  junitTestRuntimeOnlyArtifacts.forEach {
    testRuntimeOnly(it)
  }
}
