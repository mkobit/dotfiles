plugins {
  id("dotfilesbuild.kotlin.library")
}

group = "io.mkobit.ssh.script"

dependencies {
  implementation(libs.kotlin.scripting.jvm)
}
