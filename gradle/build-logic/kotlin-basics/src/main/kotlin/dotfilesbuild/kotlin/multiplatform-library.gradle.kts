package dotfilesbuild.kotlin

import dotfilesbuild.java.basics.applyDefaultJavaToolchainConfiguration
import org.jetbrains.kotlin.gradle.dsl.KotlinVersion

plugins {
  kotlin("multiplatform")
  id("io.kotest.multiplatform")
}

private fun platformOf(notation: String) =
  project.dependencies.platform(notation)

kotlin {
  jvmToolchain {
    applyDefaultJavaToolchainConfiguration()
  }
  jvm {
    withJava()
    compilerOptions {
      freeCompilerArgs.addAll(
        listOf(
          "-Xjsr305=strict",
          "-java-parameters",
        )
      )
    }
  }

  js {
    nodejs()
  }

  compilerOptions {
    allWarningsAsErrors = true
    apiVersion = KotlinVersion.KOTLIN_2_0
    freeCompilerArgs.addAll(
      listOf(
        "-progressive",
        "-Xcontext-receivers",
      )
    )
  }

  sourceSets {
    commonMain {
      dependencies {
        implementation(platformOf("io.kotest:kotest-bom:5.9.0"))
        // https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-bom
        implementation(platformOf("org.jetbrains.kotlinx:kotlinx-coroutines-bom:1.8.1"))

        implementation("io.github.microutils:kotlin-logging:2.1.15")
      }
    }

    commonTest {
      dependencies {
        implementation(kotlin("test"))
        implementation("io.kotest:kotest-framework-engine")
        implementation("io.kotest:kotest-assertions-core")
        implementation("io.kotest:kotest-property")
      }
    }

    jvmMain {
      dependencies {

      }
    }

    jvmTest {
      dependencies {
        implementation("io.kotest:kotest-runner-junit5")
      }
    }
  }
}
