import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  java
  application
  id("dotfilesbuild.kotlin.library")
}

dependencies {
  implementation(libs.guava)

  implementation(libs.jackson.core.core)
  implementation(libs.jackson.module.kotlin)

  // Try out Kodein
  implementation(libs.kodein.di.jvm)

  // Ktor
  implementation(libs.ktor.server.core)
  implementation(libs.ktor.server.netty)

  implementation(libs.kotlinx.coroutines.core)
  implementation(libs.kotlinx.coroutines.jdk8)
  implementation(libs.kotlinx.datetime)

  implementation(kotlin("stdlib-jdk8"))
  implementation(libs.retrofit2.retrofit)
  implementation(libs.retrofit2.converterJackson)
  implementation(libs.okhttp.client)

  implementation(libs.kotlinLogging)
  runtimeOnly(libs.slf4j.simple)
}

application {
  mainClass.set("com.mkobit.personalassistant.Main")
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
