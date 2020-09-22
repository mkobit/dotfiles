import dotfilesbuild.dependencies.kotlinLogging
import dotfilesbuild.dependencies.jacksonCore
import dotfilesbuild.dependencies.jacksonModule
import dotfilesbuild.dependencies.junitTestImplementationArtifacts
import dotfilesbuild.dependencies.junitTestRuntimeOnlyArtifacts
import dotfilesbuild.dependencies.slf4j
import dotfilesbuild.dependencies.useDotfilesDependencyRecommendations

plugins {
  java
  application
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.convention
}

repositories {
  maven(url = "https://dl.bintray.com/kotlin/kotlinx") {
    name = "kotlinx"
  }
}

ktlint {
  version.set("0.39.0")
}

configurations.all {
  useDotfilesDependencyRecommendations()
}

dependencies {
  implementation(jacksonCore("core"))
  implementation(jacksonModule("kotlin"))

  implementation(kotlin("compiler-embeddable"))
  implementation(kotlin("stdlib-jdk8"))
  implementation(kotlin("scripting-common"))
  implementation(kotlin("scripting-jvm"))
  implementation(kotlin("scripting-jvm-host"))

  implementation(kotlinLogging)
  implementation("com.squareup:kotlinpoet:1.6.0")

  junitTestImplementationArtifacts.forEach {
    testImplementation(it)
  }
  junitTestRuntimeOnlyArtifacts.forEach {
    testRuntimeOnly(it)
  }
  runtimeOnly(slf4j("simple"))
}

application {
  mainClassName = "com.mkobit.personalassistant.Main"
}

tasks {
  test {
    useJUnitPlatform()
  }
  distTar {
    enabled = false
  }
  distZip {
    enabled = false
  }
}
