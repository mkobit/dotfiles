plugins {
  id("dotfilesbuild.kotlin.multiplatform-library")
}

group = "io.mkobit.git.model"

kotlin {
  sourceSets {
    commonMain {
      dependencies {
        api("org.jetbrains.kotlinx:kotlinx-io-core:0.3.5")
      }
    }

    commonTest {
      dependencies {
        implementation(projects.testing.kotestSupport)
      }
    }
  }
}
