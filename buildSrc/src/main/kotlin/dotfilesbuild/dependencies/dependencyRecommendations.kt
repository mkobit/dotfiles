package dotfilesbuild.dependencies

import org.gradle.api.artifacts.Configuration

private fun Configuration.useDotfilesDependencyRecommendations() {
  val arrowKtVersion = "0.10.0"
  val jacksonVersion = "2.12.0"
  val junitJupiterVersion = "5.7.1"
  val junitPlatformVersion = "1.7.1"
  val kodeinDiVersion = "6.3.3"
  val kotlinxCoroutinesVersion = "1.4.3"
  val ktorVersion = "1.5.3"
  val okHttpVersion = "4.9.1"
  val log4jVersion = "2.14.1"
  val minutestVersion = "1.13.0"
  val retrofitVersion = "2.9.0"
  val slf4jVersion = "1.7.30"
  val striktVersion = "0.30.0"
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
    }
  }
}
