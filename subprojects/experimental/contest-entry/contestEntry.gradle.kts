import dotfilesbuild.dependencies.arrow
import dotfilesbuild.dependencies.defaultDotfilesRepositories
import dotfilesbuild.dependencies.guava
import dotfilesbuild.dependencies.kotlinLogging
import dotfilesbuild.dependencies.jacksonCore
import dotfilesbuild.dependencies.jacksonModule
import dotfilesbuild.dependencies.kodein
import dotfilesbuild.dependencies.kotlinx
import dotfilesbuild.dependencies.kotlinxCoroutines
import dotfilesbuild.dependencies.ktor
import dotfilesbuild.dependencies.slf4j
import dotfilesbuild.dependencies.useDotfilesDependencyRecommendations
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  java
  application

  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.convention
  id("org.jetbrains.gradle.plugin.idea-ext")
}

repositories {
  defaultDotfilesRepositories()
  kotlinx()
}

configurations.all {
  useDotfilesDependencyRecommendations()
}

dependencies {
  implementation(project(":chrome-debug-protocol"))

  implementation(guava)
  implementation(arrow("core-data"))
  implementation(arrow("effects-data"))
  implementation(arrow("extras-data"))
  implementation(arrow("core-extensions"))

  val googleClientVersion = "1.30.1"
  implementation("com.google.api-client:google-api-client:$googleClientVersion")
  implementation("com.google.apis:google-api-services-gmail:v1-rev20190602-$googleClientVersion")
  implementation("com.google.oauth-client:google-oauth-client-jetty:$googleClientVersion")

  implementation("com.typesafe:config:1.3.4")

  implementation(jacksonCore("core"))
  implementation(jacksonModule("kotlin"))

  implementation("org.jsoup:jsoup:1.12.1")

  implementation(kodein("di-generic-jvm"))
  implementation(ktor("client-apache"))
  implementation(ktor("client-cio"))
  implementation(ktor("client-json"))
  implementation(ktor("client-jackson"))
  implementation(ktor("client-websockets"))
  implementation(ktor("jackson"))

  implementation(kotlinxCoroutines("core"))
  implementation(kotlinxCoroutines("jdk8"))

  implementation(kotlin("stdlib-jdk8"))

  implementation(kotlinLogging)

  runtimeOnly(slf4j("simple"))
}

java {
  // https://github.com/ktorio/ktor/issues/321
  sourceCompatibility = JavaVersion.VERSION_1_8
//  sourceCompatibility = JavaVersion.VERSION_11
}

application {
  mainClassName = "com.mkobit.personalassistant.Main"
}

java {
  // https://github.com/ktorio/ktor/issues/321
  sourceCompatibility = JavaVersion.VERSION_1_8
}

tasks {
  withType<KotlinCompile> {
    kotlinOptions.jvmTarget = "1.8"
  }

  withType<Test>().configureEach {
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
