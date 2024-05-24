dependencyResolutionManagement {
  versionCatalogs {
    create("libs") {
      // Version
      version("arrow", "1.0.1")
      version("jackson.core", "2.17.1")
      version("kodein", "7.21.2")
      version("kotlin", "1.9.24")
      version("kotlinx.coroutines", "1.8.1")
      version("kotlinx.datetime", "0.6.0")
      version("ktor", "1.8.22")
      version("picoCli", "4.7.6")
      version("okhttp", "4.9.3")
      version("retrofit2", "2.9.0")
      version("slf4j", "1.7.32")

      // Plugin
      plugin("versions", "com.github.ben-manes.versions").version("0.51.0")
      plugin("kotlin.jvm", "org.jetbrains.kotlin.jvm").versionRef("kotlin")
      plugin("kotlin.multiplatform", "org.jetbrains.kotlin.multiplatform").versionRef("kotlin")
      plugin("kotlin.plugin.serialization", "org.jetbrains.kotlin.plugin.serialization").versionRef("kotlin")

      // Library (POM/platform)

      // Library (main)

      // Library (test)

      // Bundle

      library("arrow.core", "io.arrow-kt", "arrow-core").versionRef("arrow")
      library("kotlinx.datetime", "org.jetbrains.kotlinx", "kotlinx-coroutines-core").versionRef("kotlinx.coroutines")
      library("kotlinx.coroutines.core", "org.jetbrains.kotlinx", "kotlinx-datetime").versionRef("kotlinx.datetime")
      library("kotlinx.coroutines.jdk8", "org.jetbrains.kotlinx", "kotlinx-coroutines-jdk8").versionRef("kotlinxCoroutines")
      library("guava", "com.google.guava:guava:31.0.1-jre")
      library("hocon", "com.typesafe:config:1.4.1")
      library("jackson.core.core", "com.fasterxml.jackson.core", "jackson-core").versionRef("jacksonCore")
      library("jackson.core.annotations", "com.fasterxml.jackson.core", "jackson-annotations").versionRef("jacksonCore")
      library("jackson.module.kotlin", "com.fasterxml.jackson.module", "jackson-module-kotlin").versionRef("jacksonModule")
      library("kodein.di.jvm", "org.kodein.di", "kodein-di-jvm").versionRef("kodein")

      library("kotlin.js.stdlib", "org.jetbrains.kotlin", "kotlin-stdlib-js").withoutVersion()
      library("kotlin.scripting.common", "org.jetbrains.kotlin", "kotlin-scripting-common").withoutVersion()
      library("kotlin.scripting.jvm", "org.jetbrains.kotlin", "kotlin-scripting-jvm").withoutVersion()
      library("kotlin.scripting.jvmHost", "org.jetbrains.kotlin", "kotlin-scripting-jvm-host").withoutVersion()
      library("kotlin.jvm.stdlib", "org.jetbrains.kotlin", "kotlin-stdlib").withoutVersion()
      library("kotlin.jvm.jdk8", "org.jetbrains.kotlin", "kotlin-stdlib-jdk8").withoutVersion()
      library("kotlin.reflect", "org.jetbrains.kotlin", "kotlin-reflect").withoutVersion()
      library("kotlin.mp.test", "org.jetbrains.kotlin", "kotlin-test").withoutVersion()

      library("kotlinLogging", "io.github.microutils:kotlin-logging:2.1.15")
      library("kotlinPoet", "com.squareup:kotlinpoet:1.10.2")
      library("ktor.server.core", "io.ktor", "ktor-server-core").versionRef("ktor")
      library("ktor.server.netty", "io.ktor", "ktor-server-netty").versionRef("ktor")
      library("okhttp.client", "com.squareup.okhttp3", "okhttp").versionRef("okhttp")
      library("picocli.cli", "info.picocli", "picocli").versionRef("picoCli")
      library("retrofit2.retrofit", "com.squareup.retrofit2", "retrofit").versionRef("retrofit2")
      library("retrofit2.converterJackson", "com.squareup.retrofit2", "converter-jackson").versionRef("retrofit2")
      library("slf4j.simple", "org.slf4j", "slf4j-simple").versionRef("slf4j")
    }

    create("testLibs") {
      version("log4j", "2.14.1")
      version("junit.jupiter", "5.8.2")
      version("junit.platform", "1.8.2")
      version("minutest", "1.13.0")
      version("mockk", "1.12.1")
      version("strikt", "0.33.0")

      library("junit.jupiter.api", "org.junit.jupiter", "junit-jupiter-api").versionRef("junit.jupiter")
      library("junit.jupiter.params", "org.junit.jupiter", "junit-jupiter-params").versionRef("junit.jupiter")
      library("junit.jupiter.engine", "org.junit.jupiter", "junit-jupiter-engine").versionRef("junit.jupiter")
      library("junit.platform.runner", "org.junit.platform", "junit-platform-runner").versionRef("junit.platform")
      library("log4j.core", "org.apache.logging.log4j", "log4j-core").versionRef("log4j")
      library("log4j.jul", "org.apache.logging.log4j", "log4j-jul").versionRef("log4j")
      library("minutest", "dev.minutest", "minutest").versionRef("minutest")
      library("mockk", "io.mockk", "mockk").versionRef("mockk")
      library("strikt.core", "io.strikt", "strikt-core").versionRef("strikt")
//      library("strikt.gradle", "io.strikt", "strikt-gradle").versionRef("strikt") // strikt-gradle only 0.31.0
      library("strikt.gradle", "io.strikt", "strikt-gradle").version("0.31.0")
      library("strikt.jackson", "io.strikt", "strikt-jackson").versionRef("strikt")
      library("strikt.jvm", "io.strikt", "strikt-jvm").versionRef("strikt")
      library("strikt.mockk", "io.strikt", "strikt-mockk").versionRef("strikt")

      bundle("junit.implementation", listOf("junit.jupiter.api", "junit.jupiter.params"))
      bundle("junit.runtime", listOf("junit.jupiter.engine", "log4j.core", "log4j.jul"))
    }
  }
}
