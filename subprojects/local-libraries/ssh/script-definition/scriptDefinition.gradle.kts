plugins {
  `java-library`
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.library
}

group = "io.mkobit.ssh.script"

dependencies {
  implementation("org.jetbrains.kotlin:kotlin-scripting-jvm")
}
