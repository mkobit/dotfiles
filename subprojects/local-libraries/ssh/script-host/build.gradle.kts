plugins {
  `java-library`
  // id("org.jlleitschuh.gradle.ktlint")
  id("dotfilesbuild.kotlin.library")
}

group = "io.mkobit.ssh.host"

dependencies {
  implementation(projects.localLibraries.ssh.scriptDefinition)
  implementation(kotlin("scripting-common"))
  implementation(kotlin("scripting-jvm"))
  implementation(kotlin("scripting-jvm-host"))
  testImplementation(projects.localLibraries.testing.striktKotlinScripting)
}

tasks {
  test {
    val testData = layout.projectDirectory.dir("testData")
    inputs.files(testData.asFileTree).withPropertyName("testData")
    environment("TEST_DATA_DIR", testData)
  }
}
