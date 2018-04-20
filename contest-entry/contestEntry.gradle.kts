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

  implementation(DependencyInfo.jacksonCore("core"))
  implementation(DependencyInfo.jacksonModule("kotlin"))

  implementation(DependencyInfo.kodeinJvm)
  implementation(DependencyInfo.ktor("client-apache"))

  implementation(DependencyInfo.kotlinxCoroutines("core"))
  implementation(DependencyInfo.kotlinxCoroutines("jdk8"))

  implementation(DependencyInfo.cdp4j)

  implementation(kotlin("stdlib-jre8"))

  implementation(DependencyInfo.kotlinLogging)

  DependencyInfo.junitTestImplementationArtifacts.forEach {
    testImplementation(it)
  }
  DependencyInfo.junitTestRuntimeOnlyArtifacts.forEach {
    testRuntimeOnly(it)
  }
  runtimeOnly(DependencyInfo.slf4j("simple"))
}

java {
  sourceCompatibility = JavaVersion.VERSION_1_9
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
