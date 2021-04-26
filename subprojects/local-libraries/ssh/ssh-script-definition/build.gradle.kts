plugins {
  id("dotfilesbuild.kotlin.library")
}

group = "io.mkobit.ssh.script"

dependencies {
  implementation(projects.localLibraries.ssh.sshConfigGenerator)
  implementation(libs.kotlin.scripting.jvm)
  implementation(libs.kotlin.reflect)
}
