import org.jetbrains.kotlin.gradle.plugin.KotlinSourceSet

plugins {
  `java-library`
  id("dotfilesbuild.kotlin.library")
}

val generationDir = file("$buildDir/generated-source")
val generatorClasspath by configurations.creating

dependencies {
  generatorClasspath(projects.experimental.chromeDebugProtocolGenerator)
  api(libs.jackson.core.annotations)
}

tasks {
  val browserProtocol = layout.buildDirectory.file("chrome-protocol-schema/browser_protocol-1.3.json")
  val jsProtocol = layout.buildDirectory.file("chrome-protocol-schema/js_protocol-1.3.json")
  val retrieveProtocolV3 by registering {
    val commitSha = "650362400cdcc47040fb23d5d911d91b747a77c4"
    val jsUrl = "https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/$commitSha/json/js_protocol.json"
    val browserUrl = "https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/$commitSha/json/browser_protocol.json"
    inputs.property("jsUrl", jsUrl)
    inputs.property("browserUrl", browserUrl)
    outputs.files(browserProtocol, jsProtocol)
    doFirst("download protocols") {
      ant.invokeMethod("get", mapOf("src" to jsUrl, "dest" to browserProtocol.get().asFile))
      ant.invokeMethod("get", mapOf("src" to browserUrl, "dest" to jsProtocol.get().asFile))
    }
  }

  val generateCDP by registering(JavaExec::class) {
    val basePackage = "com.mkobit.cdp"
    dependsOn(retrieveProtocolV3)
    inputs.files(browserProtocol, jsProtocol)
    inputs.property("basePackage", basePackage)
    outputs.dir(generationDir)
    classpath = generatorClasspath
    mainClass = "com.mkobit.cdp.Main"
    args(
        "--basePackage", "com.mkobit.cdp",
        "--protocolJson", browserProtocol.get().asFile,
        "--protocolJson", jsProtocol.get().asFile,
        "--generationDir", generationDir
    )
  }

//  (sourceSets.main.get().getCompileTaskName("kotlin")) {
//    dependsOn(generateCDP)
//  }
}
