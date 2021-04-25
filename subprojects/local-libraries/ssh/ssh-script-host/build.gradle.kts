plugins {
  id("dotfilesbuild.kotlin.library")
}

group = "io.mkobit.ssh.host"

dependencies {
  implementation(projects.localLibraries.ssh.sshScriptDefinition)
  implementation(libs.kotlin.scripting.common)
  implementation(libs.kotlin.scripting.jvm)
  implementation(libs.kotlin.scripting.jvmHost)
  testImplementation(projects.localLibraries.testing.striktKotlinScripting)
}

tasks {
  test {
    val testData = layout.projectDirectory.dir("testData")
    inputs.files(testData.asFileTree).withPropertyName("testData")
    environment("TEST_DATA_DIR", testData)
  }
}
