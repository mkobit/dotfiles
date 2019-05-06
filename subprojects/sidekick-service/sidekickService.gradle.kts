import dotfilesbuild.DependencyInfo
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

  // Try out Kodein
  implementation(DependencyInfo.kodeinJvm)

  // Ktor
  implementation(DependencyInfo.ktor("server-core"))
  implementation(DependencyInfo.ktor("server-netty"))

//  implementation("ru.gildor.coroutines:kotlin-coroutines-retrofit:0.9.0")
  implementation(DependencyInfo.kotlinxCoroutines("core"))
  implementation(DependencyInfo.kotlinxCoroutines("jdk8"))

  implementation(kotlin("stdlib-jdk8"))
  implementation(DependencyInfo.retrofit2("retrofit"))
  implementation(DependencyInfo.retrofit2("converter-jackson"))
  implementation(DependencyInfo.okHttpClient)

  implementation(DependencyInfo.kotlinLogging)
  runtimeOnly(DependencyInfo.slf4j("simple"))
}

java {
  sourceCompatibility = JavaVersion.VERSION_11
}

kotlin {
}

application {
  mainClassName = "com.mkobit.personalassistant.Main"
}

tasks {
  withType<KotlinCompile> {
    kotlinOptions.jvmTarget = "1.8"
  }
}

listOf("distTar", "distZip").forEach { tasks[it].enabled = false }