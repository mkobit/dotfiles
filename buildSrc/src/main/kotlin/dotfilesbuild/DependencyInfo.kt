package dotfilesbuild

object DependencyInfo {
  private const val arrowVersion = "0.9.0"
  private const val jacksonVersion = "2.9.8"
  private const val googleClientVersion = "1.28.0"
  private const val junitPlatformVersion = "1.4.2"
  private const val junitJupiterVersion = "5.4.2"
  private const val junit5Log4jVersion = "2.11.2"
  private const val kodeinVersion = "6.1.0"
  private const val kotlinxCoroutinesVersion = "1.2.1"
  private const val ktorVersion = "1.1.4"
  private const val okHttpVersion = "3.14.1"
  private const val retrofitVersion = "2.5.0"
  private const val seleniumVersion = "3.11.0"
  private const val slf4jVersion = "1.7.26"

  const val googleApiClient = "com.google.api-client:google-api-client:$googleClientVersion"
  const val googleGmailServiceClient = "com.google.apis:google-api-services-gmail:v1-rev20190422-$googleClientVersion"
  const val googleOauthClient = "com.google.oauth-client:google-oauth-client-jetty:$googleClientVersion"
  const val guava = "com.google.guava:guava:27.1-jre"
  const val hocon = "com.typesafe:config:1.3.4"
  const val jsoup = "org.jsoup:jsoup:1.12.1"
  const val kotlinPoet = "com.squareup:kotlinpoet:1.2.0"
  val kodeinJvm = kodein("di-generic-jvm")
  val log4jCore = log4j("core")
  val log4jJul = log4j("jul")
  val junitPlatformRunner = junitPlatform("runner")
  val junitJupiterApi = junitJupiter("api")
  val junitJupiterEngine = junitJupiter("engine")
  val junitJupiterParams = junitJupiter("params")
  const val minutest = "dev.minutest:minutest:1.7.0"
  val okHttpClient = okHttp("okhttp")
  const val picoCli = "info.picocli:picocli:3.9.6"
  const val kotlinLogging = "io.github.microutils:kotlin-logging:1.6.26"
  private const val striktVersion = "0.20.1"
  const val strikt = "io.strikt:strikt-core:$striktVersion"
  const val striktGradle = "io.strikt:strikt-gradle:$striktVersion"

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
