plugins {
  id("dotfilesbuild.kotlin.multiplatform-library")
}

group = "io.mkobit.homedir.assembler"

val generatedRoot = layout.buildDirectory.dir("generated/config")

kotlin {
  sourceSets {
    commonMain {
      dependencies {
        implementation(libs.clikt)
        implementation(projects.shellModel.git)
      }
    }

    commonTest {
      dependencies {
        implementation(projects.testing.kotestSupport)
      }
    }
  }
}
