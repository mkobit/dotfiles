plugins {
  id("dotfilesbuild.kotlin.multiplatform-library")
}

group = "io.mkobit.testing.kotest"

kotlin {
  sourceSets {
    commonMain {
      dependencies {
        api("io.kotest:kotest-framework-engine")
      }
    }
  }
}
