import dotfilesbuild.DependencyInfo
import org.jetbrains.gradle.ext.Application
import org.jetbrains.gradle.ext.ProjectSettings
import org.jetbrains.gradle.ext.RunConfiguration
import org.jetbrains.kotlin.gradle.dsl.Coroutines
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  java
  application

  kotlin("jvm")
  id("org.jetbrains.gradle.plugin.idea-ext")
}

repositories {
  jcenter()
  maven(url = "https://dl.bintray.com/kotlin/kotlinx") {
    name = "kotlinx"
  }
}

dependencies {
  implementation(DependencyInfo.guava)
  implementation(DependencyInfo.arrow("core"))
  implementation(DependencyInfo.arrow("syntax"))
  implementation(DependencyInfo.arrow("data"))

  implementation(DependencyInfo.googleApiClient)
  implementation(DependencyInfo.googleGmailServiceClient)
  implementation(DependencyInfo.googleOauthClient)

  implementation(DependencyInfo.hocon)

  implementation(DependencyInfo.jacksonCore("core"))
  implementation(DependencyInfo.jacksonModule("kotlin"))

  implementation(DependencyInfo.jsoup)

  implementation(DependencyInfo.kodeinJvm)
  implementation(DependencyInfo.ktor("client-apache"))
  implementation(DependencyInfo.ktor("client-cio"))
  implementation(DependencyInfo.ktor("client-json"))
  implementation(DependencyInfo.ktor("client-jackson"))
  implementation(DependencyInfo.ktor("client-websocket"))
  implementation(DependencyInfo.ktor("jackson"))

  implementation(DependencyInfo.kotlinxCoroutines("core"))
  implementation(DependencyInfo.kotlinxCoroutines("jdk8"))

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
//  sourceCompatibility = JavaVersion.VERSION_11
  sourceCompatibility = JavaVersion.VERSION_11
}

application {
  mainClassName = "com.mkobit.personalassistant.Main"
}

tasks {
  test {
    useJUnitPlatform {
      excludeTags("ChromeIntegration")
    }
  }
  (run) {
    systemProperties(
        "com.mkobit.chickendinner.gmailClientJsonPath" to rootProject.file(".config/contest-entry/gmail_client_id.json"),
        "com.mkobit.chickendinner.appConfiguration" to rootProject.file(".config/contest-entry/app-config.conf"),
        "com.mkobit.chickendinner.workspaceDirectory" to file("$buildDir/contest-entry-workspace")
    )
  }
  distTar {
    enabled = false
  }
  distZip {
    enabled = false
  }
}
