import dotfilesbuild.DependencyInfo
import org.jetbrains.kotlin.gradle.plugin.KotlinSourceSet
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  `java-library`
  kotlin("jvm")
}

repositories {
  jcenter()
  mavenCentral()
}

val generationDir = file("$buildDir/generated-source")
sourceSets {
  main {
    withConvention(KotlinSourceSet::class) {
      kotlin.srcDir(generationDir)
    }
  }
}

val generatorClasspath by configurations.creating

dependencies {
  generatorClasspath(project(":chrome-debug-protocol-generator"))
  implementation(kotlin("stdlib-jdk8"))
}

java {
  // https://github.com/ktorio/ktor/issues/321
//  sourceCompatibility = JavaVersion.VERSION_1_9
  sourceCompatibility = JavaVersion.VERSION_1_8
}

tasks {
  withType<KotlinCompile>().configureEach {
    kotlinOptions.jvmTarget = "1.8"
  }

  val protocolV3 = layout.buildDirectory.file("chrome-protocol-schema/browser_protocol-1.3.json")
  val retrieveProtocolV3 by registering {
    val url = "https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/650362400cdcc47040fb23d5d911d91b747a77c4/json/js_protocol.json"
    outputs.file(protocolV3)
    inputs.property("url", url)
    doFirst("download browser protocol") {
      ant.invokeMethod("get", mapOf("src" to url, "dest" to protocolV3.get().asFile))
    }
  }

  val generateCDP by registering(JavaExec::class) {
    val basePackage = "com.mkobit.cdp"
    dependsOn(retrieveProtocolV3)
    inputs.file(protocolV3)
    inputs.property("basePackage", basePackage)
    outputs.dir(generationDir)
    classpath = generatorClasspath
    main = "com.mkobit.cdp.Main"
    args(
        "--basePackage", "com.mkobit.cdp",
        "--protocolJson", protocolV3.get().asFile,
        "--generationDir", generationDir
    )
  }

  (sourceSets.main.get().getCompileTaskName("kotlin")) {
    dependsOn(generateCDP)
  }
}
