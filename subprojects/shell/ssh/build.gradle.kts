import dotfilesbuild.utilities.home
import dotfilesbuild.io.file.Mkdir

plugins {
  id("dotfilesbuild.dotfiles-lifecycle")
  id("dotfilesbuild.kotlin.picocli-script")
  id("dotfilesbuild.io.noop")
}

tasks {
  val sshCms by registering(Mkdir::class) {
    directory.set(home.dir(".ssh/controlMaster"))
  }

  val generatedSshStaging = layout.buildDirectory.dir("generated-ssh-staging")
  (run) {
    val outputDir = layout.buildDirectory.dir("generated-ssh")
    outputs.dir(generatedSshStaging)
    args(
      "--output-dir", generatedSshStaging.get()
    )
  }

  val syncStaged by registering(Sync::class) {
    val outputDir = layout.buildDirectory.dir("generated-ssh")
    from(generatedSshStaging)
    into(outputDir)
    dependsOn(run)
  }

  dotfiles {
    dependsOn(sshCms, syncStaged)
  }
}

dependencies {
  implementation(projects.localLibraries.ssh.sshConfigScript)
}
