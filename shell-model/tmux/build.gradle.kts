plugins {
  id("dotfilesbuild.kotlin.multiplatform-library")
}

group = "io.mkobit.tmux.model"

kotlin {
  sourceSets {
    commonMain {
      dependencies {
        api(libs.kotlinx.datetime)
        api(libs.okio.common)

        implementation(project.dependencies.platform(libs.okio.bom))
      }
    }

    commonTest {
      dependencies {
        implementation(projects.testing.kotestSupport)
        implementation(libs.okio.fakefilesystem)
      }
    }
  }
}
