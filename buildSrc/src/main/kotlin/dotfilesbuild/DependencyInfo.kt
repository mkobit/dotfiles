package dotfilesbuild

@Suppress("UNUSED", "MemberVisibilityCanBePrivate")
object DependencyInfo {
  private const val arrowVersion = "0.8.2"
  private const val jacksonVersion = "2.9.8"
  private const val googleClientVersion = "1.28.0"
  private const val junitPlatformVersion = "1.4.0"
  private const val junitJupiterVersion = "5.4.0"
  private const val junit5Log4jVersion = "2.11.2"
  private const val kodeinVersion = "6.1.0"
  private const val kotlinxCoroutinesVersion = "1.0.1"
  private const val kotlinLoggingVersion = "1.6.25"
  private const val ktorVersion = "1.1.3"
  private const val okHttpVersion = "3.13.1"
  private const val retrofitVersion = "2.5.0"
  private const val seleniumVersion = "3.11.0"
  private const val slf4jVersion = "1.7.26"

  const val assertJCore = "org.assertj:assertj-core:3.10.0"
  const val assertK = "com.willowtreeapps.assertk:assertk-jvm:0.13"
  val coroutinesxCore = kotlinxCoroutines("core")
  val coroutinesxJdk8 = kotlinxCoroutines("jdk8")
  const val googleApiClient = "com.google.api-client:google-api-client:$googleClientVersion"
  const val googleGmailServiceClient = "com.google.apis:google-api-services-gmail:v1-rev20190120-$googleClientVersion"
  const val googleOauthClient = "com.google.oauth-client:google-oauth-client-jetty:$googleClientVersion"
  const val guava = "com.google.guava:guava:27.1-jre"
  const val hocon = "com.typesafe:config:1.3.3"
  const val javapoet = "com.squareup:javapoet:1.10.0"
  const val jgit = "org.eclipse.jgit:org.eclipse.jgit:5.2.0.201812061821-r"
  const val jsoup = "org.jsoup:jsoup:1.11.3"
  const val kotlinPoet = "com.squareup:kotlinpoet:1.1.0"
  val kodeinJvm = kodein("di-generic-jvm")
  val log4jCore = log4j("core")
  val log4jJul = log4j("jul")
  const val mockito = "org.mockito:mockito-core:2.24.0"
  const val mockitoKotlin = "com.nhaarman.mockitokotlin2:mockito-kotlin:2.0.0"
  val junitPlatformRunner = junitPlatform("runner")
  val junitJupiterApi = junitJupiter("api")
  val junitJupiterEngine = junitJupiter("engine")
  val junitJupiterParams = junitJupiter("params")
  const val junitPioneer = "org.junit-pioneer:junit-pioneer:0.3.0"
  val okHttpClient = okHttp("okhttp")
  val okHttpMockServer = okHttp("mockwebserver")
  const val picoCli = "info.picocli:picocli:3.9.5"
  const val kotlinLogging = "io.github.microutils:kotlin-logging:$kotlinLoggingVersion"
  const val strikt = "io.strikt:strikt-core:0.19.0"

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
