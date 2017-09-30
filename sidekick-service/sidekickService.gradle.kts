import org.jetbrains.kotlin.gradle.dsl.Coroutines
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  `java`
  id("io.ratpack.ratpack-java") version "1.5.0"
  id("com.github.ben-manes.versions") version "0.15.0"
  kotlin("jvm", "1.1.51")
}

repositories {
  jcenter()
  mavenCentral()
}

val kodeinVersion by extra { "4.1.0" }

dependencies {
  // Maybe try out Kodein?
  implementation("com.github.salomonbrys.kodein:kodein:$kodeinVersion")
  implementation("com.github.salomonbrys.kodein:kodein-jxinject:$kodeinVersion")

  implementation("org.funktionale", "funktionale-all", "1.1")
  implementation("io.webfolder", "cdp4j", "2.0.0")

  implementation(kotlin("stdlib-jre8", "1.1.51"))
  // TODO: switch when publishing to JCenter finishes - https://bintray.com/kotlin/kotlinx/kotlinx.coroutines
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:0.19")
  implementation("com.squareup.retrofit2:retrofit:2.3.0")
  implementation("com.squareup.okhttp3:okhttp:3.9.0")
  implementation("io.github.microutils:kotlin-logging:1.4.6")

  runtimeOnly("org.slf4j:slf4j-simple:1.7.25")
}

java {
  sourceCompatibility = JavaVersion.VERSION_1_8
}

kotlin {
  experimental.coroutines = Coroutines.ENABLE
}

tasks.withType(KotlinCompile::class.java) {
  kotlinOptions.jvmTarget = "1.8"
}

application {
  mainClassName = "com.mkobit.personalassistant.Main"
}
