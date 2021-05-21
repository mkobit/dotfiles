import org.gradle.accessors.dm.LibrariesForLibs
import org.gradle.accessors.dm.LibrariesForTestLibs
import org.gradle.kotlin.dsl.withType
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  `java-library`
  //  kotlin("jvm") this doesn't seem to work
  id("org.jetbrains.kotlin.jvm")
}

java {
  sourceCompatibility = JavaVersion.VERSION_11
}

tasks {
  withType<KotlinCompile>().configureEach {
    kotlinOptions {
      jvmTarget = "11"
      useIR = true
      freeCompilerArgs += listOf("-progressive")
    }
  }

  withType<Test>().configureEach {
    useJUnitPlatform {
      includeEngines("junit-jupiter")
    }
  }
}

// hack: https://github.com/gradle/gradle/issues/15383
val libs = the<LibrariesForLibs>()
val testLibs = the<LibrariesForTestLibs>()
dependencies {
  api(libs.kotlin.jvm.stdlib)
  api(libs.kotlin.jvm.jdk8)

  testImplementation(testLibs.strikt.core)
  testImplementation(testLibs.minutest)
  testImplementation(testLibs.bundles.junit.implementation)
  testRuntimeOnly(testLibs.bundles.junit.runtime)
}
