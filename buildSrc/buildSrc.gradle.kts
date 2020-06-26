import org.jetbrains.kotlin.gradle.tasks.KotlinCompile
import org.jlleitschuh.gradle.ktlint.KtlintFormatTask

plugins {
  `kotlin-dsl`
  id("org.jlleitschuh.gradle.ktlint") version "9.2.1"

  id("com.github.ben-manes.versions") version "0.28.0"
}

repositories {
  jcenter()
  gradlePluginPortal()
  mavenCentral()
}

ktlint {
  version.set("0.32.0")
}

kotlinDslPluginOptions {
  experimentalWarning.set(false)
}

java {
  sourceCompatibility = JavaVersion.VERSION_11
  targetCompatibility = JavaVersion.VERSION_11
}

fun Configuration.useDotfilesDependencyRecommendations() {
  val arrowKtVersion = "0.9.0"
  val jacksonVersion = "2.9.9"
  val junitJupiterVersion = "5.4.2"
  val junitPlatformVersion = "1.4.2"
  val kodeinDiVersion = "6.3.3"
  val kotlinxCoroutinesVersion = "1.3.0"
  val ktorVersion = "1.2.3"
  val okHttpVersion = "4.0.1"
  val log4jVersion = "2.12.0"
  val minutestVersion = "1.7.0"
  val retrofitVersion = "2.5.0"
  val slf4jVersion = "1.7.26"
  val striktVersion = "0.21.1"
  val testContainersVersion = "1.12.0"
  resolutionStrategy.eachDependency {
    when (requested.group) {
      "com.squareup.okhttp3" -> useVersion(okHttpVersion)
      "com.fasterxml.jackson.datatype" -> useVersion(jacksonVersion)
      "com.fasterxml.jackson.core" -> useVersion(jacksonVersion)
      "com.fasterxml.jackson.module" -> useVersion(jacksonVersion)
      "com.squareup.retrofit2" -> useVersion(retrofitVersion)
      "dev.minutest" -> useVersion(minutestVersion)
      "io.arrow-kt" -> useVersion(arrowKtVersion)
      "io.ktor" -> useVersion(ktorVersion)
      "io.strikt" -> useVersion(striktVersion)
      "org.apache.logging.log4j" -> useVersion(log4jVersion)
      "org.jetbrains.kotlinx" -> when {
        requested.name.startsWith("kotlinx-coroutines") && !requested.name.contains("io") -> useVersion(
          kotlinxCoroutinesVersion)
      }
      "org.kodein.di" -> useVersion(kodeinDiVersion)
      "org.junit.jupiter" -> useVersion(junitJupiterVersion)
      "org.junit.platform" -> useVersion(junitPlatformVersion)
      "org.slf4j" -> useVersion(slf4jVersion)
      "org.testcontainers" -> useVersion(testContainersVersion)
    }
  }
}

configurations.all { useDotfilesDependencyRecommendations() }

dependencies {
  // https://github.com/gradle/kotlin-dsl/issues/430
  fun gradlePlugin(id: String, version: String): String = "$id:$id.gradle.plugin:$version"
  implementation(gradlePlugin("org.jetbrains.kotlin.jvm", "1.3.72"))

  implementation("io.github.microutils:kotlin-logging:1.7.10")

  implementation("io.arrow-kt:arrow-core-data")
  implementation("io.arrow-kt:arrow-core-extensions")

  implementation("com.squareup.retrofit2:retrofit:2.5.0")
  implementation("com.squareup.okhttp3:okhttp")
  implementation("org.eclipse.jgit:org.eclipse.jgit:5.7.0.202003110725-r")

  testImplementation("io.mockk:mockk:1.10.0")

  testImplementation("com.mkobit.gradle.test:gradle-test-kotlin-extensions:0.7.0")
  testImplementation("io.strikt:strikt-core")
  testImplementation("io.strikt:strikt-gradle")

  testImplementation("dev.minutest:minutest")
  testImplementation("org.junit.jupiter:junit-jupiter-api")
  testImplementation("org.junit.jupiter:junit-jupiter-params")

  testRuntimeOnly("org.junit.jupiter:junit-jupiter-engine")
  testRuntimeOnly("org.apache.logging.log4j:log4j-core")
  testRuntimeOnly("org.apache.logging.log4j:log4j-jul")
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
            reject("Release candidate")
          }
        }
      }
    }
  }

  assemble {
    dependsOn(withType<KtlintFormatTask>())
  }

  withType<KtlintFormatTask>().configureEach {
    onlyIf { project.hasProperty("ktlintFormatBuildSrc") }
  }

  dependencyUpdates {
    onlyIf { project.hasProperty("updateBuildSrc") }
  }

  build {
    dependsOn(dependencyUpdates)
  }

  withType<KotlinCompile>().configureEach {
    kotlinOptions {
      jvmTarget = "11"
      freeCompilerArgs += listOf("-progressive")
    }
  }

  test {
    useJUnitPlatform()
    systemProperty("java.util.logging.manager", "org.apache.logging.log4j.jul.LogManager")
  }
}

gradlePlugin {
  plugins {
    register("dotfilesbuild.git-vcs") {
      id = name
      implementationClass = "dotfilesbuild.io.git.GitVersionControlManagementPlugin"
    }
    register("dotfilesbuild.self-update") {
      id = name
      implementationClass = "dotfilesbuild.versioning.SelfUpdatePlugin"
    }
    register("dotfilesbuild.vcs-management") {
      id = name
      implementationClass = "dotfilesbuild.io.vcs.VersionControlManagementPlugin"
    }
  }
}
