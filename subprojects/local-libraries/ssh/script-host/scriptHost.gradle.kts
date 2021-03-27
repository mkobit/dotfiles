plugins {
  `java-library`
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.library
}

group = "io.mkobit.ssh.host"

dependencies {
  implementation(project(":local-libraries:ssh:script-definition"))
  implementation("org.jetbrains.kotlin:kotlin-scripting-common")
  implementation("org.jetbrains.kotlin:kotlin-scripting-jvm")
  implementation("org.jetbrains.kotlin:kotlin-scripting-jvm-host")
}

tasks {
  test {
    val testData = layout.projectDirectory.dir("testData")
    inputs.files(testData.asFileTree).withPropertyName("testData")
    environment("TEST_DATA_DIR", testData)
  }
}
