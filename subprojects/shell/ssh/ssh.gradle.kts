import dotfilesbuild.dependencies.useDotfilesDependencyRecommendations
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

configurations.all {
  useDotfilesDependencyRecommendations()
}

dependencies {
  implementation(projects.localLibraries.ssh.configGenerator)
}
