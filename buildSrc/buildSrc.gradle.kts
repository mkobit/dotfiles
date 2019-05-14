import org.jetbrains.kotlin.gradle.tasks.KotlinCompile
import org.jlleitschuh.gradle.ktlint.KtlintFormatTask

plugins {
  `kotlin-dsl`
  id("org.jlleitschuh.gradle.ktlint") version "8.0.0"

  id("com.github.ben-manes.versions") version "0.21.0"
}

repositories {
  jcenter()
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
  resolutionStrategy.eachDependency {
    when (requested.group) {
      "dev.minutest" -> useVersion("1.7.0")
      "io.arrow-kt" -> useVersion("0.8.2")
      "org.junit.jupiter" -> useVersion("5.4.2")
      "org.junit.platform" -> useVersion("1.4.2")
      "io.strikt" -> useVersion("0.20.1")
      "org.apache.logging.log4j" -> useVersion("2.11.2")
    }
  }
}

dependencies {
  implementation("io.github.microutils:kotlin-logging:1.6.26")

  implementation("io.arrow-kt:arrow-core")
  implementation("io.arrow-kt:arrow-effects")
  implementation("io.arrow-kt:arrow-syntax")
  implementation("io.arrow-kt:arrow-typeclasses")

  implementation("com.squareup.retrofit2:retrofit:2.5.0")
  implementation("com.squareup.okhttp3:okhttp:3.14.1")
  implementation("org.eclipse.jgit:org.eclipse.jgit:5.3.1.201904271842-r")

  testImplementation("io.mockk:mockk:1.9.3")

  testImplementation("com.mkobit.gradle.test:assertj-gradle:0.2.0")
  testImplementation("com.mkobit.gradle.test:gradle-test-kotlin-extensions:0.6.0")
  testImplementation("org.assertj:assertj-core:3.12.2")
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

  if (hasProperty("ktlintFormatBuildSrc")) {
    assemble {
      dependsOn(withType<KtlintFormatTask>())
    }
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
