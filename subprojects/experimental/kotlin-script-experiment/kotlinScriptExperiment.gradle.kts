import dotfilesbuild.DependencyInfo

plugins {
  java
  application
  id("org.jlleitschuh.gradle.ktlint")
  kotlin("jvm")
}

repositories {
  jcenter()
  mavenCentral()
  maven(url = "https://dl.bintray.com/kotlin/kotlinx") {
    name = "kotlinx"
  }
}

ktlint {
  version.set("0.32.0")
}

dependencies {
  implementation(DependencyInfo.jacksonCore("core"))
  implementation(DependencyInfo.jacksonModule("kotlin"))

  implementation(kotlin("compiler-embeddable"))
  implementation(kotlin("stdlib-jdk8"))
  implementation(kotlin("scripting-common"))
  implementation(kotlin("scripting-jvm"))
  implementation(kotlin("scripting-jvm-host"))

  implementation(DependencyInfo.kotlinLogging)
  implementation(DependencyInfo.kotlinPoet)

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
//  sourceCompatibility = JavaVersion.VERSION_11
  sourceCompatibility = JavaVersion.VERSION_11
}

application {
  mainClassName = "com.mkobit.personalassistant.Main"
}

tasks {
  test {
    useJUnitPlatform()
  }
  distTar {
    enabled = false
  }
  distZip {
    enabled = false
  }
}
