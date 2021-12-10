enableFeaturePreview("VERSION_CATALOGS")

dependencyResolutionManagement {
  versionCatalogs {
    create("libs") {
      version("arrow", "1.0.1")
      version("jacksonCore", "2.13.0")
      version("jacksonModule", "2.13.0")
      version("kodein", "7.9.0")
      version("kotlinxCoroutines", "1.5.2")
      version("kotlinxDatetime", "0.3.1")
      version("ktor", "1.6.7")
      version("picoCli", "4.6.2")
      version("okhttp", "4.9.3")
      version("retrofit2", "2.9.0")
      version("slf4j", "1.7.32")

      alias("arrow.core").to("io.arrow-kt", "arrow-core").versionRef("arrow")
      alias("kotlinx.datetime").to("org.jetbrains.kotlinx", "kotlinx-coroutines-core").versionRef("kotlinxCoroutines")
      alias("kotlinx.coroutines.core").to("org.jetbrains.kotlinx", "kotlinx-datetime").versionRef("kotlinxDatetime")
      alias("kotlinx.coroutines.jdk8").to("org.jetbrains.kotlinx", "kotlinx-coroutines-jdk8").versionRef("kotlinxCoroutines")
      alias("guava").to("com.google.guava:guava:31.0.1-jre")
      alias("hocon").to("com.typesafe:config:1.4.1")
      alias("jackson.core.core").to("com.fasterxml.jackson.core", "jackson-core").versionRef("jacksonCore")
      alias("jackson.core.annotations").to("com.fasterxml.jackson.core", "jackson-annotations").versionRef("jacksonCore")
      alias("jackson.module.kotlin").to("com.fasterxml.jackson.module", "jackson-module-kotlin").versionRef("jacksonModule")
      alias("kodein.di.jvm").to("org.kodein.di", "kodein-di-jvm").versionRef("kodein")

      alias("kotlin.js.stdlib").to("org.jetbrains.kotlin", "kotlin-stdlib-js").withoutVersion()
      alias("kotlin.scripting.common").to("org.jetbrains.kotlin", "kotlin-scripting-common").withoutVersion()
      alias("kotlin.scripting.jvm").to("org.jetbrains.kotlin", "kotlin-scripting-jvm").withoutVersion()
      alias("kotlin.scripting.jvmHost").to("org.jetbrains.kotlin", "kotlin-scripting-jvm-host").withoutVersion()
      alias("kotlin.jvm.stdlib").to("org.jetbrains.kotlin", "kotlin-stdlib").withoutVersion()
      alias("kotlin.jvm.jdk8").to("org.jetbrains.kotlin", "kotlin-stdlib-jdk8").withoutVersion()
      alias("kotlin.reflect").to("org.jetbrains.kotlin", "kotlin-reflect").withoutVersion()
      alias("kotlin.mp.test").to("org.jetbrains.kotlin", "kotlin-test").withoutVersion()

      alias("kotlinLogging").to("io.github.microutils:kotlin-logging:2.1.15")
      alias("kotlinPoet").to("com.squareup:kotlinpoet:1.10.2")
      alias("ktor.server.core").to("io.ktor", "ktor-server-core").versionRef("ktor")
      alias("ktor.server.netty").to("io.ktor", "ktor-server-netty").versionRef("ktor")
      alias("okhttp.client").to("com.squareup.okhttp3", "okhttp").versionRef("okhttp")
      alias("picocli.cli").to("info.picocli", "picocli").versionRef("picoCli")
      alias("retrofit2.retrofit").to("com.squareup.retrofit2", "retrofit").versionRef("retrofit2")
      alias("retrofit2.converterJackson").to("com.squareup.retrofit2", "converter-jackson").versionRef("retrofit2")
      alias("slf4j.simple").to("org.slf4j", "slf4j-simple").versionRef("slf4j")
    }

    create("testLibs") {
      version("log4j", "2.14.1")
      version("junit.jupiter", "5.8.2")
      version("junit.platform", "1.8.2")
      version("minutest", "1.13.0")
      version("mockk", "1.12.1")
      version("strikt", "0.33.0")

      alias("junit.jupiter.api").to("org.junit.jupiter", "junit-jupiter-api").versionRef("junit.jupiter")
      alias("junit.jupiter.params").to("org.junit.jupiter", "junit-jupiter-params").versionRef("junit.jupiter")
      alias("junit.jupiter.engine").to("org.junit.jupiter", "junit-jupiter-engine").versionRef("junit.jupiter")
      alias("junit.platform.runner").to("org.junit.platform", "junit-platform-runner").versionRef("junit.platform")
      alias("log4j.core").to("org.apache.logging.log4j", "log4j-core").versionRef("log4j")
      alias("log4j.jul").to("org.apache.logging.log4j", "log4j-jul").versionRef("log4j")
      alias("minutest").to("dev.minutest", "minutest").versionRef("minutest")
      alias("mockk").to("io.mockk", "mockk").versionRef("mockk")
      alias("strikt.core").to("io.strikt", "strikt-core").versionRef("strikt")
//      alias("strikt.gradle").to("io.strikt", "strikt-gradle").versionRef("strikt") // strikt-gradle only 0.31.0
      alias("strikt.gradle").to("io.strikt", "strikt-gradle").version("0.31.0")
      alias("strikt.jackson").to("io.strikt", "strikt-jackson").versionRef("strikt")
      alias("strikt.jvm").to("io.strikt", "strikt-jvm").versionRef("strikt")
      alias("strikt.mockk").to("io.strikt", "strikt-mockk").versionRef("strikt")

      bundle("junit.implementation", listOf("junit.jupiter.api", "junit.jupiter.params"))
      bundle("junit.runtime", listOf("junit.jupiter.engine", "log4j.core", "log4j.jul"))
    }
  }
}
