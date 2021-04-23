import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  `java-library`
  id("org.jlleitschuh.gradle.ktlint")
  id("dotfilesbuild.kotlin.library")
}

dependencies {
  implementation(libs.guava)
  implementation(libs.kotlinPoet)
  implementation(libs.picocli.cli)

  implementation(libs.jackson.core.core)
  implementation(libs.jackson.module.kotlin)

  implementation(kotlin("stdlib-jdk8"))

  implementation(libs.kotlinLogging)
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
