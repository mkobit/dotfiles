package dotfilesbuild.kotlin

import org.jetbrains.kotlin.gradle.dsl.KotlinVersion
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
  kotlin("multiplatform")
//  id("dotfilesbuild.java.default-settings")
}

private fun platformFor(notation: String) =
  project.dependencies.platform(notation)

kotlin {
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
    browser()
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
        implementation(platformFor("io.kotest:kotest-bom:5.9.0"))
        // https://mvnrepository.com/artifact/org.jetbrains.kotlinx/kotlinx-coroutines-bom
        implementation(platformFor("org.jetbrains.kotlinx:kotlinx-coroutines-bom:1.8.1"))

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
