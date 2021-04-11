import dotfilesbuild.dependencies.guava
import dotfilesbuild.dependencies.kotlinLogging
import dotfilesbuild.dependencies.jacksonCore
import dotfilesbuild.dependencies.jacksonModule
import dotfilesbuild.dependencies.picoCli
import dotfilesbuild.dependencies.useDotfilesDependencyRecommendations
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  `java-library`
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.library
}

configurations.all {
  useDotfilesDependencyRecommendations()
}

dependencies {
  implementation(guava)
  implementation("com.squareup:kotlinpoet:1.7.2")
  implementation(picoCli)

  implementation(jacksonCore("core"))
  implementation(jacksonModule("kotlin"))

  implementation(kotlin("stdlib-jdk8"))

  implementation(kotlinLogging)
}

java {
  // https://github.com/ktorio/ktor/issues/321
  sourceCompatibility = JavaVersion.VERSION_1_8
}

tasks {
  withType<KotlinCompile> {
    kotlinOptions.jvmTarget = "1.8"
  }
}
