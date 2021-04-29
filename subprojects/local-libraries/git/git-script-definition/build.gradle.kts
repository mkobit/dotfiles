plugins {
  id("dotfilesbuild.kotlin.library")
}

group = "io.mkobit.git.script"

dependencies {
  implementation(projects.localLibraries.git.gitConfigGenerator)
  implementation(libs.kotlin.scripting.jvm)
  implementation(libs.kotlin.reflect)
}
