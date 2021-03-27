import dotfilesbuild.home
import dotfilesbuild.property
import dotfilesbuild.process.FileTreeExpandingCommandLineArgumentProvider

plugins {
  dotfilesbuild.`dotfiles-lifecycle`
  dotfilesbuild.kotlin.`picocli-script`
  id("org.jlleitschuh.gradle.ktlint")
}

val workspace: Directory = home.dir("Workspace")
val personalWorkspaceDirectory: Directory = workspace.dir("personal")
val workWorkspaceDirectory: Directory = workspace.dir("work")
val codeLabWorkspaceDirectory: Directory = workspace.dir("code_lab")

val shell = Attribute.of("shell.config", Usage::class.java)

val scriptConfig by configurations.creating {
  attributes {
    attribute(shell, objects.named(Usage::class, "git"))
  }
}

dependencies {
  implementation(project(":local-libraries:git:config-generator"))
  implementation("com.typesafe:config:1.4.1")
  scriptConfig(project(":shell:external-configuration"))
}

tasks {
  (run) {
    val outputDir = layout.buildDirectory.dir("generated-git")
    outputs.dir(outputDir)
    argumentProviders.add(
      FileTreeExpandingCommandLineArgumentProvider(
        objects.property("--config-file"),
        scriptConfig.asFileTree
      )
    )
    args(
      "--output-dir", outputDir.get(),
      "--global-excludes-file", layout.projectDirectory.file("gitconfig/gitignore_global.dotfile"),
      "--work-dir", workWorkspaceDirectory.dir("**"),
      "--code-lab-dir", codeLabWorkspaceDirectory.dir("**"),
      "--personal-dir", personalWorkspaceDirectory.dir("**"),
      "--dotfiles-dir", rootProject.layout.projectDirectory.dir("**")
    )
  }

  dotfiles {
    dependsOn(run)
  }
}
