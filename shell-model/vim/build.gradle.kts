plugins {
  id("dotfilesbuild.kotlin.multiplatform-library")
}

group = "io.mkobit.vim.model"

kotlin {
  sourceSets {
    commonMain {
      dependencies {
        api(libs.kotlinx.io.core)
      }
    }

    commonTest {
      dependencies {
        implementation(projects.testing.kotestSupport)
      }
    }
  }
}
