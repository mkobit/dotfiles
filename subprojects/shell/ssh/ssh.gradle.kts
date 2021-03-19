import dotfilesbuild.home
import dotfilesbuild.io.file.Mkdir

plugins {
  dotfilesbuild.`dotfiles-lifecycle`
  dotfilesbuild.kotlin.`picocli-script`
  id("org.jlleitschuh.gradle.ktlint")
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
  implementation(project(":local-libraries:ssh-config-generator"))
}
