import org.gradle.kotlin.dsl.`embedded-kotlin`
import org.jetbrains.kotlin.gradle.dsl.Coroutines

plugins {
  `java-library`
  `kotlin-dsl`
  `java-gradle-plugin`
}

repositories {
  jcenter()
  mavenCentral()
}

java {
  sourceCompatibility = JavaVersion.VERSION_1_9
  targetCompatibility = JavaVersion.VERSION_1_9
}

val junitPlatformVersion: String = "1.1.0"
val junitJupiterVersion: String = "5.1.0"
val junit5Log4jVersion: String = "2.10.0"

val junitPlatformRunner = mapOf("group" to "org.junit.platform", "name" to "junit-platform-runner", "version" to junitPlatformVersion)
val junitJupiterApi = mapOf("group" to "org.junit.jupiter", "name" to "junit-jupiter-api", "version" to junitJupiterVersion)
val junitJupiterParams = mapOf("group" to "org.junit.jupiter", "name" to "junit-jupiter-params", "version" to junitJupiterVersion)

val junitTestImplementationArtifacts = listOf(
    junitPlatformRunner,
    junitJupiterApi,
    junitJupiterParams
)

val assertJCore = "org.assertj:assertj-core:3.9.1"
val mockitoCore = "org.mockito:mockito-core:2.15.0"
val mockitoKotlin = "com.nhaarman:mockito-kotlin:1.5.0"
val junitJupiterEngine = mapOf("group" to "org.junit.jupiter", "name" to "junit-jupiter-engine", "version" to junitJupiterVersion)
val log4jCore = mapOf("group" to "org.apache.logging.log4j", "name" to "log4j-core", "version" to junit5Log4jVersion)
val log4jJul = mapOf("group" to "org.apache.logging.log4j", "name" to "log4j-jul", "version" to junit5Log4jVersion)

val junitTestRuntimeOnlyArtifacts = listOf(
    junitJupiterEngine,
    log4jCore,
    log4jJul
)


val coroutinesVersion by extra { "0.22.5" }
dependencies {
  val arrowVersion = "0.6.0"
  implementation("io.arrow-kt:arrow-core:$arrowVersion")
  implementation("io.arrow-kt:arrow-instances:$arrowVersion")
  implementation("io.arrow-kt:arrow-effects:$arrowVersion")
  implementation("io.arrow-kt:arrow-syntax:$arrowVersion")
  implementation("io.arrow-kt:arrow-typeclasses:$arrowVersion")
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:$coroutinesVersion")
  implementation("com.squareup.retrofit2:retrofit:2.3.0")
  implementation("com.squareup.okhttp3:okhttp:3.10.0")
  implementation("io.github.microutils:kotlin-logging:1.5.3")
  implementation("org.eclipse.jgit:org.eclipse.jgit:4.10.0.201712302008-r")
  // https://mvnrepository.com/artifact/com.google.guava/guava
  implementation("com.google.guava:guava:24.1-jre")

  testImplementation("com.mkobit.gradle.test:assertj-gradle:0.2.0")
  testImplementation("com.mkobit.gradle.test:gradle-test-kotlin-extensions:0.3.0")
  testImplementation(assertJCore)
  testImplementation(mockitoCore)
  testImplementation(mockitoKotlin)
  junitTestImplementationArtifacts.forEach {
    testImplementation(it)
  }
  junitTestRuntimeOnlyArtifacts.forEach {
    testRuntimeOnly(it)
  }
}

kotlin {
  experimental.coroutines = Coroutines.ENABLE
}

tasks {
  "test"(Test::class) {
    useJUnitPlatform()
    systemProperty("java.util.logging.manager", "org.apache.logging.log4j.jul.LogManager")
  }
}

gradlePlugin {
  plugins.invoke {
    "home" {
      id = "dotfilesbuild.locations"
      implementationClass = "dotfilesbuild.LocationsPlugin"
    }
    "fileManagement" {
      id = "dotfilesbuild.file-management"
      implementationClass = "dotfilesbuild.io.file.FileManagementPlugin"
    }
    "gitVcs" {
      id = "dotfilesbuild.git-vcs"
      implementationClass = "dotfilesbuild.io.git.GitVersionControlManagementPlugin"
    }
    "keepassProgram" {
      id = "dotfilesbuild.keepass"
      implementationClass = "dotfilesbuild.keepass.KeepassProgramPlugin"
    }
    "intellijProgram" {
      id = "dotfilesbuild.intellij"
      implementationClass = "dotfilesbuild.intellij.IntelliJProgramPlugin"
    }
    "selfUpdate" {
      id = "dotfilesbuild.self-update"
      implementationClass = "dotfilesbuild.versioning.SelfUpdatePlugin"
    }
    "vcsManagement" {
      id = "dotfilesbuild.vcs-management"
      implementationClass = "dotfilesbuild.io.vcs.VersionControlManagementPlugin"
    }
  }
}
