package dotfilesbuild

@Suppress("UNUSED", "MemberVisibilityCanBePrivate")
object DependencyInfo {
  const val arrowVersion = "0.7.2"
  const val javapoetVersion = "1.10.0"
  const val jacksonVersion = "2.9.6"
  const val junitPlatformVersion = "1.2.0"
  const val junitJupiterVersion = "5.2.0"
  const val junit5Log4jVersion = "2.11.0"
  const val kodeinVersion = "5.2.0"
  const val kotlinxCoroutinesVersion = "0.23.4"
  const val kotlinLoggingVersion = "1.5.4"
  const val ktorVersion = "0.9.3"
  const val okHttpVersion = "3.11.0"
  const val retrofitVersion = "2.4.0"
  const val seleniumVersion = "3.11.0"
  const val slf4jVersion = "1.7.25"

  const val assertJCore = "org.assertj:assertj-core:3.10.0"
  const val assertK = "com.willowtreeapps.assertk:assertk:0.10"
  const val guava = "com.google.guava:guava:25.1-jre"
  const val javapoet = "com.squareup:javapoet:$javapoetVersion"
  const val jgit = "org.eclipse.jgit:org.eclipse.jgit:4.10.0.201712302008-r"
  const val jsoup = "org.jsoup:jsoup:1.11.3"
  const val kotlinPoet = "com.squareup:kotlinpoet:0.7.0"
  val kodeinJvm = kodein("di-generic-jvm")
  const val mockito = "org.mockito:mockito-core:2.17.0"
  const val mockitoKotlin = "com.nhaarman:mockito-kotlin:1.5.0"
  val junitPlatformRunner = junitPlatform("runner")
  val junitJupiterApi = junitJupiter("api")
  val junitJupiterEngine = junitJupiter("engine")
  val junitJupiterParams = junitJupiter("params")
  val coroutinesxCore = kotlinxCoroutines("core")
  val coroutinesxJdk8 = kotlinxCoroutines("jdk8")
  val okHttpClient = okHttp("okhttp")
  val okHttpMockServer = okHttp("mockwebserver")
  const val kotlinLogging = "io.github.microutils:kotlin-logging:$kotlinLoggingVersion"
  val log4jCore = log4j("core")
  val log4jJul = log4j("jul")

  val junitTestImplementationArtifacts = listOf(
      junitPlatformRunner,
      junitJupiterApi,
      junitJupiterParams
  )

  val junitTestRuntimeOnlyArtifacts = listOf(
      junitJupiterEngine,
      log4jCore,
      log4jJul
  )

  fun arrow(module: String) = "io.arrow-kt:arrow-$module:$arrowVersion"
  fun jacksonCore(module: String, version: String = jacksonVersion) = "com.fasterxml.jackson.core:jackson-$module:$version"
  fun jacksonModule(module: String, version: String = jacksonVersion) = "com.fasterxml.jackson.module:jackson-module-$module:$version"
  fun junitJupiter(module: String) = "org.junit.jupiter:junit-jupiter-$module:$junitJupiterVersion"
  fun junitPlatform(module: String) = "org.junit.platform:junit-platform-$module:$junitPlatformVersion"
  fun kodein(module: String) = "org.kodein.di:kodein-$module:$kodeinVersion"
  fun ktor(module: String) = "io.ktor:ktor-$module:$ktorVersion"
  fun kotlinxCoroutines(module: String) = "org.jetbrains.kotlinx:kotlinx-coroutines-$module:$kotlinxCoroutinesVersion"
  fun log4j(module: String) = "org.apache.logging.log4j:log4j-$module:$junit5Log4jVersion"
  fun okHttp(module: String) = "com.squareup.okhttp3:$module:$okHttpVersion"
  fun retrofit2(module: String) = "com.squareup.retrofit2:$module:$retrofitVersion"
  fun selenium(module: String) = "org.seleniumhq.selenium:selenium-$module:$seleniumVersion"
  fun slf4j(module: String) = "org.slf4j:slf4j-$module:$slf4jVersion"
}
