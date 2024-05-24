package dotfilesbuild.kotlin
import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import org.jetbrains.kotlin.gradle.dsl.KotlinVersion
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  id("dotfilesbuild.java.basics.default-settings")
  id("org.jetbrains.kotlin.jvm")
}

kotlin {
  compilerOptions {
    allWarningsAsErrors = true
    apiVersion = KotlinVersion.KOTLIN_2_0
    jvmTarget = java.toolchain.languageVersion.map {
      JvmTarget.fromTarget(it.toString())
    }
    freeCompilerArgs.addAll(
      listOf(
        "-progressive",
        "-Xjsr305=strict",
        "-java-parameters",
        "-Xcontext-receivers",
      )
    )
  }
}

val kotestBomCoordinates = "io.kotest:kotest-bom:5.9.0"

dependencies {
  implementation(platform(kotestBomCoordinates))
  implementation("io.github.microutils:kotlin-logging:2.1.15")
}

testing {
  suites {
    val test by getting(JvmTestSuite::class) {
      dependencies {
        implementation("io.mockk:mockk:1.13.11")

        implementation(platform(kotestBomCoordinates))
        implementation("io.kotest:kotest-runner-junit5")
        implementation("io.kotest:kotest-assertions-core")
        implementation("io.kotest:kotest-property")
      }
    }
  }
}
