import org.gradle.kotlin.dsl.`embedded-kotlin`
import org.jetbrains.kotlin.gradle.dsl.Coroutines

plugins {
  `java-library`
  `kotlin-dsl`
  `java-gradle-plugin`
  id("com.github.ben-manes.versions") version "0.17.0"
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
val junit5Log4jVersion: String = "2.11.0"

val junitPlatformRunner = "org.junit.platform:junit-platform-runner:$junitPlatformVersion"
val junitJupiterApi = "org.junit.jupiter:junit-jupiter-api:$junitJupiterVersion"
val junitJupiterParams = "org.junit.jupiter:junit-jupiter-params:$junitJupiterVersion"

val junitTestImplementationArtifacts = listOf(
    junitPlatformRunner,
    junitJupiterApi,
    junitJupiterParams
)

val assertJCore = "org.assertj:assertj-core:3.9.1"
val mockitoCore = "org.mockito:mockito-core:2.18.0"
val mockitoKotlin = "com.nhaarman:mockito-kotlin:1.5.0"
val junitJupiterEngine = "org.junit.jupiter:junit-jupiter-engine:$junitJupiterVersion"
val log4jCore = "org.apache.logging.log4j:log4j-core:$junit5Log4jVersion"
val log4jJul = "org.apache.logging.log4j:log4j-jul:$junit5Log4jVersion"

val junitTestRuntimeOnlyArtifacts = listOf(
    junitJupiterEngine,
    log4jCore,
    log4jJul
)

// uncomment when needed
//val build by tasks.getting {
//  dependsOn("dependencyUpdates")
//}

val coroutinesVersion by extra { "0.22.5" }
val arrowVersion by extra { "0.7.1" }
dependencies {
  implementation("io.arrow-kt:arrow-core:$arrowVersion")
  implementation("io.arrow-kt:arrow-effects:$arrowVersion")
  implementation("io.arrow-kt:arrow-syntax:$arrowVersion")
  implementation("io.arrow-kt:arrow-typeclasses:$arrowVersion")
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:$coroutinesVersion")
  implementation("com.squareup.retrofit2:retrofit:2.4.0")
  implementation("com.squareup.okhttp3:okhttp:3.10.0")
  implementation("io.github.microutils:kotlin-logging:1.5.4")
  implementation("org.eclipse.jgit:org.eclipse.jgit:4.11.0.201803080745-r")
  // https://mvnrepository.com/artifact/com.google.guava/guava
  implementation("com.google.guava:guava:24.1-jre")

  testImplementation("com.mkobit.gradle.test:assertj-gradle:0.2.0")
  testImplementation("com.mkobit.gradle.test:gradle-test-kotlin-extensions:0.5.0")
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
