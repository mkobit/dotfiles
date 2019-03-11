import dotfilesbuild.DependencyInfo
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  `java-library`
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
  implementation(DependencyInfo.kotlinPoet)
  implementation(DependencyInfo.picoCli)

  implementation(DependencyInfo.jacksonCore("core"))
  implementation(DependencyInfo.jacksonModule("kotlin"))

  implementation(kotlin("stdlib-jdk8"))

  implementation(DependencyInfo.kotlinLogging)

  testImplementation(DependencyInfo.strikt)
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
  sourceCompatibility = JavaVersion.VERSION_1_8
}

tasks {
  withType<Test>().configureEach {
    useJUnitPlatform()
  }
}
