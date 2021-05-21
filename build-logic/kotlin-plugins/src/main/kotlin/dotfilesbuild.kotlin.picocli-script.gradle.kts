import org.gradle.accessors.dm.LibrariesForLibs
import org.gradle.accessors.dm.LibrariesForTestLibs
import org.gradle.kotlin.dsl.application
import org.gradle.kotlin.dsl.dependencies
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  application
  id("org.jetbrains.kotlin.jvm")
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

  (run) {
    mainClass.set(provider { "${project.group}.${project.name}.Main" })
  }
}

// hack: https://github.com/gradle/gradle/issues/15383
val libs = the<LibrariesForLibs>()
val testLibs = the<LibrariesForTestLibs>()
dependencies {
  implementation(libs.picocli.cli)
  api(libs.kotlin.jvm.stdlib)
  api(libs.kotlin.jvm.jdk8)

  testImplementation(testLibs.strikt.core)
  testImplementation(testLibs.minutest)
  testImplementation(testLibs.bundles.junit.implementation)
  testRuntimeOnly(testLibs.bundles.junit.runtime)
}
