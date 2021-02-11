import dotfilesbuild.home

plugins {
  dotfilesbuild.`dotfiles-lifecycle`
  dotfilesbuild.kotlin.`picocli-script`
  id("org.jlleitschuh.gradle.ktlint")
}

group = "shell.git.config"

val workspace = home.dir("Workspace")
val personalWorkspaceDirectory: Directory = workspace.dir("personal")
val workWorkspaceDirectory: Directory = workspace.dir("work")
val codeLabWorkspaceDirectory: Directory = workspace.dir("code_lab")

application {
  mainClass.set("shell.git.config.Main")
}

tasks {
  (run) {
    val outputDir = layout.buildDirectory.dir("generated-git")
    outputs.dir(outputDir)
    // todo: ** kind of messy
    args(
      "--output-dir", outputDir.get(),
      "--global-excludes-file", layout.projectDirectory.file("gitconfig/gitignore_global.dotfile"),
      "--work-dir", workWorkspaceDirectory.dir("**"),
      "--code-lab-dir", codeLabWorkspaceDirectory.dir("**"),
      "--personal-dir", personalWorkspaceDirectory.dir("**"),
      "--work-config", home.file(".gitconfig_work"),
      "--dotfiles-dir", rootProject.layout.projectDirectory.dir("**")
    )
  }

  dotfiles {
    dependsOn(run)
  }
}

dependencies {
  implementation(project(":local-libraries:git-config-generator"))
}
