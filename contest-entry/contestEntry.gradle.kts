import dotfilesbuild.DependencyInfo
import org.jetbrains.kotlin.gradle.dsl.Coroutines
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  java
  application
  kotlin("jvm")
}

repositories {
  jcenter()
  mavenCentral()
  maven(url = "http://dl.bintray.com/kotlin/ktor") {
    name = "ktor"
  }
  maven(url = "https://dl.bintray.com/kotlin/kotlinx") {
    name = "kotlinx"
  }
}

dependencies {
  implementation(DependencyInfo.guava)
  implementation(DependencyInfo.arrow("core"))
  implementation(DependencyInfo.arrow("syntax"))
  implementation(DependencyInfo.arrow("data"))

  implementation(DependencyInfo.jacksonCore("core"))
  implementation(DependencyInfo.jacksonModule("kotlin"))

  implementation(DependencyInfo.kodeinJvm)
  implementation(DependencyInfo.ktor("client-apache"))
  implementation(DependencyInfo.ktor("client-cio"))
  implementation(DependencyInfo.ktor("client-websocket"))
  implementation(DependencyInfo.ktor("jackson"))
  implementation(DependencyInfo.ktor("client-json"))

  implementation(DependencyInfo.kotlinxCoroutines("core"))
  implementation(DependencyInfo.kotlinxCoroutines("jdk8"))

  implementation(kotlin("stdlib-jdk8"))

  implementation(DependencyInfo.kotlinLogging)

  testImplementation(DependencyInfo.assertK)
  DependencyInfo.junitTestImplementationArtifacts.forEach {
    testImplementation(it)
  }
  DependencyInfo.junitTestRuntimeOnlyArtifacts.forEach {
    testRuntimeOnly(it)
  }
  runtimeOnly(DependencyInfo.slf4j("simple"))
}

java {
  // https://github.com/ktorio/ktor/issues/321
//  sourceCompatibility = JavaVersion.VERSION_1_9
  sourceCompatibility = JavaVersion.VERSION_1_8
}

kotlin {
  experimental.coroutines = Coroutines.ENABLE
}

application {
  mainClassName = "com.mkobit.personalassistant.Main"
}

tasks {
  withType<KotlinCompile> {
    kotlinOptions.jvmTarget = "1.8"
  }
  "test"(Test::class) {
    useJUnitPlatform()
  }
}

listOf("distTar", "distZip").forEach { tasks[it].enabled = false }
