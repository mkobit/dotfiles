package dotfilesbuild.kotlin

import gradle.kotlin.dsl.accessors._6dceb40dbc73ea30c501a1d6b8a3e27d.testImplementation
import gradle.kotlin.dsl.accessors._6dceb40dbc73ea30c501a1d6b8a3e27d.testRuntimeOnly
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

dependencies {
  api(kotlin("stdlib"))
  api(kotlin("stdlib-jdk8"))

  testImplementation("io.strikt:strikt-core:0.30.1")
  testImplementation("dev.minutest:minutest:1.13.0")

  val junitJupiterVersion = "5.7.1"
  val junitPlatformVersion = "1.7.1"
  val log4jVersion = "2.14.1"
  listOf(
    "org.junit.platform:junit-platform-runner:$junitPlatformVersion",
    "org.junit.jupiter:junit-jupiter-api:$junitJupiterVersion",
    "org.junit.jupiter:junit-jupiter-params:$$junitJupiterVersion",
  ).forEach {
    testImplementation(it)
  }
  listOf(
    "org.junit.jupiter:junit-jupiter-engine:$junitJupiterVersion",
    "org.apache.logging.log4j:log4j-core:$log4jVersion",
    "org.apache.logging.log4j:log4j-jul:$log4jVersion",
  ).forEach {
    testRuntimeOnly(it)
  }
}
