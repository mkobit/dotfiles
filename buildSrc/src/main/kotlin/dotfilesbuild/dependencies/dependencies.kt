package dotfilesbuild.dependencies

import org.gradle.api.artifacts.dsl.DependencyHandler

const val picoCli = "info.picocli:picocli:4.0.1"
const val guava = "com.google.guava:guava:28.0-jre"
const val kotlinLogging = "io.github.microutils:kotlin-logging:1.7.2"

fun DependencyHandler.arrow(module: String, version: String? = null) = "io.arrow-kt:arrow-$module${version?.let { ":$version" } ?: ""}"
fun DependencyHandler.jacksonCore(module: String, version: String? = null) = "com.fasterxml.jackson.core:jackson-$module${version?.let { ":$version" } ?: ""}"
fun DependencyHandler.jacksonModule(module: String, version: String? = null) = "com.fasterxml.jackson.module:jackson-module-$module${version?.let { ":$version" } ?: ""}"
fun DependencyHandler.junitJupiter(module: String, version: String? = null) = "org.junit.jupiter:junit-jupiter-$module${version?.let { ":$version" } ?: ""}"
fun DependencyHandler.junitPlatform(module: String, version: String? = null) = "org.junit.platform:junit-platform-$module${version?.let { ":$version" } ?: ""}"
fun DependencyHandler.kodein(module: String, version: String? = null) = "org.kodein.di:kodein-$module${version?.let { ":$version" } ?: ""}"
fun DependencyHandler.ktor(module: String, version: String? = null) = "io.ktor:ktor-$module${version?.let { ":$version" } ?: ""}"
fun DependencyHandler.kotlinxCoroutines(module: String, version: String? = null) = "org.jetbrains.kotlinx:kotlinx-coroutines-$module${version?.let { ":$version" } ?: ""}"
fun DependencyHandler.log4j(module: String, version: String? = null) = "org.apache.logging.log4j:log4j-$module${version?.let { ":$version" } ?: ""}"
fun DependencyHandler.okHttp(module: String, version: String? = null) = "com.squareup.okhttp3:$module${version?.let { ":$version" } ?: ""}"
fun DependencyHandler.retrofit2(module: String, version: String? = null) = "com.squareup.retrofit2:$module${version?.let { ":$version" } ?: ""}"
fun DependencyHandler.selenium(module: String, version: String? = null) = "org.seleniumhq.selenium:selenium-$module${version?.let { ":$version" } ?: ""}"
fun DependencyHandler.slf4j(module: String, version: String? = null) = "org.slf4j:slf4j-$module${version?.let { ":$version" } ?: ""}"
fun DependencyHandler.strikt(module: String, version: String? = null) = "io.strikt:strikt-$module${version?.let { ":$version" } ?: ""}"

val DependencyHandler.junitTestImplementationArtifacts get() = listOf(
  junitPlatform("runner"),
  junitJupiter("api"),
  junitJupiter("params")
)

val DependencyHandler.junitTestRuntimeOnlyArtifacts get() = listOf(
  junitJupiter("engine"),
  log4j("core"),
  log4j("jul")
)
