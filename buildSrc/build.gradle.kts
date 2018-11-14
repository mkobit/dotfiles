import com.github.benmanes.gradle.versions.updates.DependencyUpdatesTask
import org.jetbrains.kotlin.gradle.dsl.Coroutines

plugins {
  `java-library`
  `kotlin-dsl`
  `kotlin-dsl-precompiled-script-plugins`
  `java-gradle-plugin`

  id("com.github.ben-manes.versions") version "0.20.0"
}

repositories {
  jcenter()
  mavenCentral()
}

java {
  sourceCompatibility = JavaVersion.VERSION_1_9
  targetCompatibility = JavaVersion.VERSION_1_9
}

val junitPlatformVersion: String = "1.3.1"
val junitJupiterVersion: String = "5.3.1"
val junit5Log4jVersion: String = "2.11.1"

val junitPlatformRunner = "org.junit.platform:junit-platform-runner:$junitPlatformVersion"
val junitJupiterApi = "org.junit.jupiter:junit-jupiter-api:$junitJupiterVersion"
val junitJupiterParams = "org.junit.jupiter:junit-jupiter-params:$junitJupiterVersion"

val junitTestImplementationArtifacts = listOf(
    junitPlatformRunner,
    junitJupiterApi,
    junitJupiterParams
)

val assertJCore = "org.assertj:assertj-core:3.11.1"
val junitPioneer = "org.junit-pioneer:junit-pioneer:0.3.0"
val log4jCore = "org.apache.logging.log4j:log4j-core:$junit5Log4jVersion"
val log4jJul = "org.apache.logging.log4j:log4j-jul:$junit5Log4jVersion"
val mockitoCore = "org.mockito:mockito-core:2.23.0"
val mockitoKotlin = "com.nhaarman.mockitokotlin2:mockito-kotlin:2.0.0"
val junitJupiterEngine = "org.junit.jupiter:junit-jupiter-engine:$junitJupiterVersion"
val strikt = "io.strikt:strikt-core:0.17.0"

val junitTestRuntimeOnlyArtifacts = listOf(
    junitJupiterEngine,
    log4jCore,
    log4jJul
)

val dependencyUpdates by tasks.getting(DependencyUpdatesTask::class) {
  val rejectPatterns = listOf("alpha", "beta", "rc", "cr", "m").map { qualifier ->
    Regex("(?i).*[.-]$qualifier[.\\d-]*")
  }
  resolutionStrategy {
    componentSelection {
      all {
        if (rejectPatterns.any { it.matches(candidate.version) }) {
          this.reject("Release candidate")
        }
      }
    }
  }
}

val build by tasks.getting {
//  dependsOn("dependencyUpdates") // uncomment when want to get dependency updates for buildSrc project
}

val coroutinesVersion by extra { "1.0.0" }
val arrowVersion by extra { "0.7.3" }
dependencies {
  implementation("io.arrow-kt:arrow-core:$arrowVersion")
  implementation("io.arrow-kt:arrow-effects:$arrowVersion")
  implementation("io.arrow-kt:arrow-syntax:$arrowVersion")
  implementation("io.arrow-kt:arrow-typeclasses:$arrowVersion")
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:$coroutinesVersion")
  implementation("com.squareup.retrofit2:retrofit:2.4.0")
  implementation("com.squareup.okhttp3:okhttp:3.11.0")
  implementation("io.github.microutils:kotlin-logging:1.6.10")
  implementation("org.eclipse.jgit:org.eclipse.jgit:5.1.3.201810200350-r")
  // https://mvnrepository.com/artifact/com.google.guava/guava
  implementation("com.google.guava:guava:27.0-jre")

  testImplementation("com.mkobit.gradle.test:assertj-gradle:0.2.0")
  testImplementation("com.mkobit.gradle.test:gradle-test-kotlin-extensions:0.6.0")
  testImplementation(assertJCore)
  testImplementation(mockitoCore)
  testImplementation(mockitoKotlin)
  testImplementation(junitPioneer)
  testImplementation(strikt)
  junitTestImplementationArtifacts.forEach {
    testImplementation(it)
  }
  junitTestRuntimeOnlyArtifacts.forEach {
    testRuntimeOnly(it)
  }
}

tasks {
  "test"(Test::class) {
    useJUnitPlatform()
    systemProperty("java.util.logging.manager", "org.apache.logging.log4j.jul.LogManager")
  }
}

gradlePlugin {
  plugins {
    register("binManaged") {
      id = "dotfilesbuild.shell.managed-bin"
      implementationClass = "dotfilesbuild.shell.ManagedBinPlugin"
    }
    register("binSourceControlled") {
      id = "dotfilesbuild.shell.source-bin"
      implementationClass = "dotfilesbuild.shell.SourceControlledBinPlugin"
    }
    register("binUnmanaged") {
      id = "dotfilesbuild.shell.unmanaged-bin"
      implementationClass = "dotfilesbuild.shell.UnmanagedBinPlugin"
    }
    register("fileManagement") {
      id = "dotfilesbuild.file-management"
      implementationClass = "dotfilesbuild.io.file.FileManagementPlugin"
    }
    register("gitVcs") {
      id = "dotfilesbuild.git-vcs"
      implementationClass = "dotfilesbuild.io.git.GitVersionControlManagementPlugin"
    }
    register("intellijProgram") {
      id = "dotfilesbuild.intellij"
      implementationClass = "dotfilesbuild.intellij.IntelliJProgramPlugin"
    }
    register("locations") {
      id = "dotfilesbuild.locations"
      implementationClass = "dotfilesbuild.LocationsPlugin"
    }
    register("keepassProgram") {
      id = "dotfilesbuild.keepass"
      implementationClass = "dotfilesbuild.keepass.KeepassProgramPlugin"
    }
    register("selfUpdate") {
      id = "dotfilesbuild.self-update"
      implementationClass = "dotfilesbuild.versioning.SelfUpdatePlugin"
    }
    register("vcsManagement") {
      id = "dotfilesbuild.vcs-management"
      implementationClass = "dotfilesbuild.io.vcs.VersionControlManagementPlugin"
    }
    register("binGeneratedZsh") {
      id = "dotfilesbuild.shell.generated-zsh"
      implementationClass = "dotfilesbuild.shell.GeneratedZshrcSourceFilePlugin"
    }
  }
}
