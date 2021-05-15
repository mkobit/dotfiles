plugins {
  id("dotfilesbuild.kotlin.library")
}

group = "io.mkobit.git.script"

dependencies {
  api(projects.localLibraries.git.gitConfigGenerator)
  implementation(libs.kotlin.scripting.common)
  implementation(libs.kotlin.scripting.jvm)
  implementation(libs.kotlin.scripting.jvmHost)
  implementation(libs.kotlin.reflect)
  testImplementation(projects.localLibraries.testing.striktKotlinScripting)
}

tasks {
  test {
    val testData = layout.projectDirectory.dir("testData")
    inputs.dir(testData).withPropertyName("testData")
    environment("TEST_DATA_DIR", testData)
  }
}
