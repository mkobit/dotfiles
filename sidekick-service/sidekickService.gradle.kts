import org.jetbrains.kotlin.gradle.dsl.Coroutines
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  `java`
  `application`
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
  maven(url = "http://dl.bintray.com/salomonbrys/kodein") {
    name = "kodein"
  }
}

val ktorVersion by extra { "0.9.1" }
val jacksonVersion by extra { "2.9.4" }
val kodeinVersion by extra { "4.1.0" }
val coroutinesVersion by extra { "0.22.5" }
val retrofitVersion by extra { "2.3.0" }

dependencies {
  implementation("com.google.guava:guava:24.0-jre")

  implementation("com.fasterxml.jackson.core:jackson-core:$jacksonVersion")
  implementation("com.fasterxml.jackson.module:jackson-module-kotlin:$jacksonVersion")

  // Try out Kodein
  implementation("com.github.salomonbrys.kodein:kodein:$kodeinVersion")
  implementation("com.github.salomonbrys.kodein:kodein-jxinject:$kodeinVersion")

  // Ktor
  implementation("io.ktor:ktor-server-core:$ktorVersion")
  implementation("io.ktor:ktor-server-netty:$ktorVersion")

  implementation("ru.gildor.coroutines:kotlin-coroutines-retrofit:0.9.0")
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:$coroutinesVersion")
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines-jdk8:$coroutinesVersion")

  implementation("io.webfolder", "cdp4j", "2.2.4")

  implementation(kotlin("stdlib-jre8"))
  // TODO: switch when publishing to JCenter finishes - https://bintray.com/kotlin/kotlinx/kotlinx.coroutines
  implementation("com.squareup.retrofit2:retrofit:$retrofitVersion")
  implementation("com.squareup.retrofit2:converter-jackson:$retrofitVersion")
  implementation("com.squareup.okhttp3:okhttp:3.10.0")

  implementation("io.github.microutils:kotlin-logging:1.5.3")

  runtimeOnly("org.slf4j:slf4j-simple:1.7.25")
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
}

listOf("distTar", "distZip").forEach { tasks[it].enabled = false }
