plugins {
  `java-library`
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.library
}

group = "io.mkobit.ssh.host"

dependencies {
  implementation(project(":local-libraries:ssh:script-definition"))
  implementation(kotlin("scripting-common"))
  implementation(kotlin("scripting-jvm"))
  implementation(kotlin("scripting-jvm-host"))
  testImplementation(project(":local-libraries:testing:strikt-kotlin-scripting"))
}

tasks {
  test {
    val testData = layout.projectDirectory.dir("testData")
    inputs.files(testData.asFileTree).withPropertyName("testData")
    environment("TEST_DATA_DIR", testData)
  }
}
