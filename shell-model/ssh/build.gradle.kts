plugins {
  id("dotfilesbuild.kotlin.multiplatform-library")
}

group = "io.mkobit.ssh.model"

kotlin {
  sourceSets {
    commonMain {
      dependencies {
//        api(libs.kotlinx.io.core)
        api(libs.okio.common)
        api(libs.kotlinx.datetime)
        api(project.dependencies.platform(libs.okio.bom))
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
