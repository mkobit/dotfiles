import dotfilesbuild.dependencies.defaultDotfilesRepositories
import dotfilesbuild.dependencies.guava
import dotfilesbuild.dependencies.jacksonCore
import dotfilesbuild.dependencies.jacksonModule
import dotfilesbuild.dependencies.kodein
import dotfilesbuild.dependencies.kotlinLogging
import dotfilesbuild.dependencies.kotlinxCoroutines
import dotfilesbuild.dependencies.ktor
import dotfilesbuild.dependencies.okHttp
import dotfilesbuild.dependencies.retrofit2
import dotfilesbuild.dependencies.slf4j
import dotfilesbuild.dependencies.useDotfilesDependencyRecommendations
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  java
  application
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.library
}

repositories {
  defaultDotfilesRepositories()
}

configurations.all {
  useDotfilesDependencyRecommendations()
}

dependencies {
  implementation(guava)

  implementation(jacksonCore("core"))
  implementation(jacksonModule("kotlin"))

  // Try out Kodein
  implementation(kodein("di-generic-jvm"))

  // Ktor
  implementation(ktor("server-core"))
  implementation(ktor("server-netty"))

  implementation(kotlinxCoroutines("core"))
  implementation(kotlinxCoroutines("jdk8"))

  implementation(kotlin("stdlib-jdk8"))
  implementation(retrofit2("retrofit"))
  implementation(retrofit2("converter-jackson"))
  implementation(okHttp("okhttp"))

  implementation(kotlinLogging)
  runtimeOnly(slf4j("simple"))
}

application {
  mainClassName = "com.mkobit.personalassistant.Main"
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

listOf("distTar", "distZip").forEach { tasks[it].enabled = false }
