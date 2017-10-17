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
}

val vertxVersion by extra { "3.4.2" }
val kodeinVersion by extra { "4.1.0" }
val coroutinesVersion by extra { "0.19.1" }
val retrofitVersion by extra { "2.3.0" }

dependencies {
  implementation("com.google.guava:guava:23.0")

  implementation("com.fasterxml.jackson.core:jackson-core:2.9.1")
  implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.9.0")

  // Maybe try out Kodein?
  implementation("com.github.salomonbrys.kodein:kodein:$kodeinVersion")
  implementation("com.github.salomonbrys.kodein:kodein-jxinject:$kodeinVersion")

  implementation("io.vertx:vertx-core:$vertxVersion")
  implementation("io.vertx:vertx-web:$vertxVersion")
  implementation("io.vertx:vertx-lang-kotlin:$vertxVersion")
//  implementation("io.vertx:vertx-lang-kotlin-coroutines:$vertxVersion")

  implementation("ru.gildor.coroutines:kotlin-coroutines-retrofit:0.7.1")
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:$coroutinesVersion")
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines-jdk8:$coroutinesVersion")
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines-jdk8:$coroutinesVersion")

  implementation("io.webfolder", "cdp4j", "2.0.0")

  implementation(kotlin("stdlib-jre8"))
  // TODO: switch when publishing to JCenter finishes - https://bintray.com/kotlin/kotlinx/kotlinx.coroutines
  implementation("com.squareup.retrofit2:retrofit:$retrofitVersion")
  implementation("com.squareup.retrofit2:converter-jackson:$retrofitVersion")
  implementation("com.squareup.okhttp3:okhttp:3.9.0")

  implementation("io.github.microutils:kotlin-logging:1.4.6")
  implementation("org.funktionale", "funktionale-all", "1.1")

  runtimeOnly("org.slf4j:slf4j-simple:1.7.25")
}

java {
  sourceCompatibility = JavaVersion.VERSION_1_9
}

kotlin {
  experimental.coroutines = Coroutines.ENABLE
}

// Vert.x docs
// 1. https://github.com/vert-x3/vertx-lang-kotlin/blob/master/vertx-lang-kotlin-coroutines/src/main/kotlin/example/Example.kt
// 2. http://vertx.io/docs/vertx-core/kotlin/
// 3. https://github.com/vert-x3/vertx-lang-kotlin/blob/master/vertx-lang-kotlin-coroutines/src/main/asciidoc/kotlin/index.adoc
application {
  mainClassName = "io.vertx.core.Launcher"
}

val mainVerticleName = "com.mkobit.personalassistant.Main"

tasks {
  withType<KotlinCompile> {
    kotlinOptions.jvmTarget = "1.8"
  }

  "run"(JavaExec::class) {
    args = listOf("run", mainVerticleName,
    "--launcher-class=${application.mainClassName}",
    "--redeploy=src/**/*.*",
    "--on-redeploy=../gradlew assemble")
  }
}

listOf("distTar", "distZip").forEach { tasks[it].enabled = false }
