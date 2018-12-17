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

val junitPlatformVersion: String = "1.3.2"
val junitJupiterVersion: String = "5.3.2"
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
val mockitoCore = "org.mockito:mockito-core:2.23.4"
val mockitoKotlin = "com.nhaarman.mockitokotlin2:mockito-kotlin:2.0.0"
val junitJupiterEngine = "org.junit.jupiter:junit-jupiter-engine:$junitJupiterVersion"
val strikt = "io.strikt:strikt-core:0.17.0"

val junitTestRuntimeOnlyArtifacts = listOf(
    junitJupiterEngine,
    log4jCore,
    log4jJul
)

val coroutinesVersion by extra { "1.0.1" }
val arrowVersion by extra { "0.8.1" }
dependencies {
  implementation("io.arrow-kt:arrow-core:$arrowVersion")
  implementation("io.arrow-kt:arrow-effects:$arrowVersion")
  implementation("io.arrow-kt:arrow-syntax:$arrowVersion")
  implementation("io.arrow-kt:arrow-typeclasses:$arrowVersion")
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:$coroutinesVersion")
  implementation("com.squareup.retrofit2:retrofit:2.5.0")
  implementation("com.squareup.okhttp3:okhttp:3.12.0")
  implementation("io.github.microutils:kotlin-logging:1.6.10")
  implementation("org.eclipse.jgit:org.eclipse.jgit:5.2.0.201812061821-r")

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
  dependencyUpdates {
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

  build {
//    dependsOn(dependencyUpdates) // uncomment when want to get dependency updates for buildSrc project
  }

  test {
    useJUnitPlatform()
    systemProperty("java.util.logging.manager", "org.apache.logging.log4j.jul.LogManager")
  }
}

gradlePlugin {
  plugins {
    register("dotfilesbuild.file-management") {
      id = name
      implementationClass = "dotfilesbuild.io.file.FileManagementPlugin"
    }
    register("dotfilesbuild.git-vcs") {
      id = name
      implementationClass = "dotfilesbuild.io.git.GitVersionControlManagementPlugin"
    }
    register("dotfilesbuild.intellij") {
      id = name
      implementationClass = "dotfilesbuild.intellij.IntelliJProgramPlugin"
    }
    register("dotfilesbuild.locations") {
      id = name
      implementationClass = "dotfilesbuild.LocationsPlugin"
    }
    register("dotfilesbuild.keepass") {
      id = name
      implementationClass = "dotfilesbuild.keepass.KeepassProgramPlugin"
    }
    register("dotfilesbuild.kubernetes.kubectl-managed-binary") {
      id = name
      implementationClass = "dotfilesbuild.kubernetes.KubectlProgramPlugin"
    }
    register("dotfilesbuild.self-update") {
      id = name
      implementationClass = "dotfilesbuild.versioning.SelfUpdatePlugin"
    }
    register("dotfilesbuild.shell.generated-zsh") {
      id = name
      implementationClass = "dotfilesbuild.shell.GeneratedZshrcSourceFilePlugin"
    }
    register("dotfilesbuild.shell.managed-bin") {
      id = name
      implementationClass = "dotfilesbuild.shell.ManagedBinPlugin"
    }
    register("dotfilesbuild.shell.source-bin") {
      id = name
      implementationClass = "dotfilesbuild.shell.SourceControlledBinPlugin"
    }
    register("dotfilesbuild.shell.unmanaged-bin") {
      id = name
      implementationClass = "dotfilesbuild.shell.UnmanagedBinPlugin"
    }
    register("dotfilesbuild.shell.zsh-aliases-and-functions") {
      id = name
      implementationClass = "dotfilesbuild.shell.ZshAliasesAndFunctionsPlugin"
    }
    register("dotfilesbuild.vcs-management") {
      id = name
      implementationClass = "dotfilesbuild.io.vcs.VersionControlManagementPlugin"
    }
  }
}
