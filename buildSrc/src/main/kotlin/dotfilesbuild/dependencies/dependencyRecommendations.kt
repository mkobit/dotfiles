package dotfilesbuild.dependencies

import org.gradle.api.artifacts.Configuration

fun Configuration.useDotfilesDependencyRecommendations() {
  val arrowKtVersion = "0.9.0"
  val jacksonVersion = "2.9.9"
  val junitJupiterVersion = "5.4.2"
  val junitPlatformVersion = "1.4.2"
  val kodeinDiVersion = "6.3.3"
  val kotlinxCoroutinesVersion = "1.3.0"
  val ktorVersion = "1.4.0"
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
          kotlinxCoroutinesVersion
        )
      }
      "org.kodein.di" -> useVersion(kodeinDiVersion)
      "org.junit.jupiter" -> useVersion(junitJupiterVersion)
      "org.junit.platform" -> useVersion(junitPlatformVersion)
      "org.slf4j" -> useVersion(slf4jVersion)
      "org.testcontainers" -> useVersion(testContainersVersion)
    }
  }
}
