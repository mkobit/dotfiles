import org.jetbrains.kotlin.gradle.tasks.KotlinCompile
import org.jlleitschuh.gradle.ktlint.tasks.KtLintFormatTask

plugins {
  `kotlin-dsl`
  id("org.jlleitschuh.gradle.ktlint") version "10.0.0"

  id("com.github.ben-manes.versions") version "0.38.0"
}

repositories {
  jcenter()
  gradlePluginPortal()
  mavenCentral()
}

ktlint {
  version.set("0.41.0")
  filter {
    exclude { element -> element.file.path.contains("generated-sources/") }
  }
}

kotlinDslPluginOptions {
  jvmTarget.set("1.8")
  experimentalWarning.set(false)
}

java {
  sourceCompatibility = JavaVersion.VERSION_1_8
  targetCompatibility = JavaVersion.VERSION_1_8
}

fun Configuration.useBuildSrcDependencies() {
  val arrowKtVersion = "0.10.0"
  val junitJupiterVersion = "5.7.0"
  val junitPlatformVersion = "1.7.0"
  val okHttpVersion = "4.9.0"
  val log4jVersion = "2.12.0"
  val minutestVersion = "1.11.0"
  val slf4jVersion = "1.7.26"
  val striktVersion = "0.26.1"
  resolutionStrategy.eachDependency {
    when (requested.group) {
      "com.squareup.okhttp3" -> useVersion(okHttpVersion)
      "dev.minutest" -> useVersion(minutestVersion)
      "io.arrow-kt" -> useVersion(arrowKtVersion)
      "io.strikt" -> useVersion(striktVersion)
      "org.apache.logging.log4j" -> useVersion(log4jVersion)
      "org.junit.jupiter" -> useVersion(junitJupiterVersion)
      "org.junit.platform" -> useVersion(junitPlatformVersion)
      "org.slf4j" -> useVersion(slf4jVersion)
    }
  }
}

configurations.all { useBuildSrcDependencies() }

dependencies {
  // https://github.com/gradle/kotlin-dsl/issues/430
  fun gradlePlugin(id: String, version: String): String = "$id:$id.gradle.plugin:$version"
  implementation(gradlePlugin("org.jetbrains.kotlin.jvm", "1.4.21-2"))

  implementation("com.typesafe:config:1.4.1")

  implementation("io.github.microutils:kotlin-logging:1.12.0")

  implementation("io.arrow-kt:arrow-core")
  implementation("io.arrow-kt:arrow-syntax")

  implementation("com.squareup.okhttp3:okhttp")
  implementation("org.eclipse.jgit:org.eclipse.jgit:5.9.0.202009080501-r")

  testImplementation("io.mockk:mockk:1.10.0")

  testImplementation("com.mkobit.gradle.test:gradle-test-kotlin-extensions:0.8.0")
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
    dependsOn(withType<KtLintFormatTask>())
  }

  withType<KtLintFormatTask>().configureEach {
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
    register("dotfilesbuild.configuration") {
      id = name
      implementationClass = "dotfilesbuild.config.ConfigurationPlugin"
    }
    register("dotfilesbuild.git-vcs") {
      id = name
      implementationClass = "dotfilesbuild.io.git.GitVersionControlManagementPlugin"
    }
    register("dotfilesbuild.vcs-management") {
      id = name
      implementationClass = "dotfilesbuild.io.vcs.VersionControlManagementPlugin"
    }
  }
}
