plugins {
  id("dotfilesbuild.kotlin.library")
}

group = "io.mkobit.ssh.script"

dependencies {
  api(projects.localLibraries.ssh.sshConfigGenerator)
  implementation(libs.kotlin.scripting.common)
  implementation(libs.kotlin.scripting.jvm)
  implementation(libs.kotlin.scripting.jvmHost)
  implementation(libs.kotlin.reflect)
}
