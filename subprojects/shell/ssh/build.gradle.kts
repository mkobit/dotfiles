import dotfilesbuild.utilities.home
import dotfilesbuild.io.file.Mkdir

plugins {
  id("dotfilesbuild.dotfiles-lifecycle")
  id("dotfilesbuild.kotlin.picocli-script")
  // id("org.jlleitschuh.gradle.ktlint")
  id("dotfilesbuild.io.noop")
}

tasks {
  val sshCms by registering(Mkdir::class) {
    directory.set(home.dir(".ssh/controlMaster"))
  }

  (run) {
    val outputDir = layout.buildDirectory.dir("generated-ssh")
    outputs.dir(outputDir)
    args(
      "--output-dir", outputDir.get()
    )
  }

  dotfiles {
    dependsOn(sshCms, run)
  }
}

dependencies {
  implementation(projects.localLibraries.ssh.sshConfigScript)
}
