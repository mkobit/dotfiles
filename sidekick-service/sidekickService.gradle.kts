import org.jetbrains.kotlin.gradle.dsl.Coroutines
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  `java`
  id("io.ratpack.ratpack-java") version "1.5.0"
  id("com.github.ben-manes.versions") version "0.15.0"
  kotlin("jvm", "1.1.50")
  kotlin("kapt", "1.1.50")
}

repositories {
  jcenter()
  mavenCentral()
}

val daggerVersion = "2.11"

kapt {
  generateStubs = true
}

dependencies {
  kapt("com.google.dagger", "dagger-compiler", daggerVersion)

  implementation("com.google.dagger", "dagger", daggerVersion)
  implementation(kotlin("stdlib-jre8", "1.1.50"))
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines:0.18")
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
