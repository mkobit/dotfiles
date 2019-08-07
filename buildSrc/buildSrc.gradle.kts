import org.jetbrains.kotlin.gradle.tasks.KotlinCompile
import org.jlleitschuh.gradle.ktlint.KtlintFormatTask

plugins {
  `kotlin-dsl`
  id("org.jlleitschuh.gradle.ktlint") version "8.2.0"

  id("com.github.ben-manes.versions") version "0.22.0"
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

configurations.all {
  // copy/paste from dependencyRecommendations.kt for now
  val arrowKtVersion = "0.9.0"
  val jacksonVersion = "2.9.9"
  val junitJupiterVersion = "5.4.2"
  val junitPlatformVersion = "1.4.2"
  val kodeinDiVersion = "6.3.3"
  val kotlinxCoroutinesVersion = "1.2.1"
  val ktorVersion = "1.2.2"
  val okHttpVersion = "4.0.1"
  val log4jVersion = "2.12.0"
  val minutestVersion = "1.7.0"
  val retrofitVersion = "2.5.0"
  val slf4jVersion = "1.7.26"
  val striktVersion = "0.21.1"
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
    }
  }
}

dependencies {
  // https://github.com/gradle/kotlin-dsl/issues/430
  fun gradlePlugin(id: String, version: String): String = "$id:$id.gradle.plugin:$version"
  implementation(gradlePlugin("org.jetbrains.kotlin.jvm", "1.3.41"))

  implementation("io.github.microutils:kotlin-logging:1.6.26")

  implementation("io.arrow-kt:arrow-core-data")
  implementation("io.arrow-kt:arrow-core-extensions")

  implementation("com.squareup.retrofit2:retrofit:2.5.0")
  implementation("com.squareup.okhttp3:okhttp")
  implementation("org.eclipse.jgit:org.eclipse.jgit:5.4.0.201906121030-r")

  testImplementation("io.mockk:mockk:1.9.3")

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
