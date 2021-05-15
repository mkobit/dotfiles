import dotfilesbuild.utilities.property
import dotfilesbuild.process.FileTreeExpandingCommandLineArgumentProvider

plugins {
  id("dotfilesbuild.dotfiles-lifecycle")
  id("dotfilesbuild.kotlin.picocli-script")
}

val shell = Attribute.of("shell.config", Usage::class.java)

val scriptConfig by configurations.creating {
  attributes {
    attribute(shell, objects.named(Usage::class, "git"))
  }
}

dependencies {
  implementation(projects.localLibraries.git.gitConfigScript)
  scriptConfig(projects.shell.externalConfiguration)
}

tasks {
  val generatedSshStaging = layout.buildDirectory.dir("generated-git-staging")
  (run) {
    outputs.dir(generatedSshStaging)
    argumentProviders.add(
      FileTreeExpandingCommandLineArgumentProvider(
        objects.property("--config-file"),
        scriptConfig.asFileTree
      )
    )
    args(
      "--output-dir", generatedSshStaging.get(),
      "--global-excludes-file", layout.projectDirectory.file("gitconfig/gitignore_global.dotfile"),
      "--dotfiles-dir", rootProject.layout.projectDirectory.dir("**")
    )
  }
  val syncStaged by registering(Sync::class) {
    val outputDir = layout.buildDirectory.dir("generated-git")
    from(generatedSshStaging)
    into(outputDir)
    dependsOn(run)
  }

  dotfiles {
    // add [include] directive to ~/.gitconfig by running command
    // git config --file ~/.gitconfig include.path <path to includes file>
    dependsOn(syncStaged)
  }
}
