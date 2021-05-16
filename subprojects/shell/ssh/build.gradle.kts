import dotfilesbuild.utilities.home
import dotfilesbuild.io.file.Mkdir
import dotfilesbuild.process.FileTreeExpandingCommandLineArgumentProvider
import dotfilesbuild.utilities.property

plugins {
  id("dotfilesbuild.dotfiles-lifecycle")
  id("dotfilesbuild.kotlin.picocli-script")
  id("dotfilesbuild.io.noop")
}

val shell = Attribute.of("shell.config", Usage::class.java)

val scriptConfig by configurations.creating {
  attributes {
    attribute(shell, objects.named(Usage::class, "ssh"))
  }
}

dependencies {
  implementation(projects.localLibraries.ssh.sshConfigScript)
  scriptConfig(projects.shell.externalConfiguration)
}

tasks {
  val sshCms by registering(Mkdir::class) {
    directory.set(home.dir(".ssh/controlMaster"))
  }

  // Ssh config files can't really be "relative".
  // The Include directive either treats it as relative to ~/.ssh/ or absolute.
  val generatedSsh = layout.buildDirectory.dir("generated-ssh")
  (run) {
    outputs.dir(generatedSsh)
    argumentProviders.add(
      FileTreeExpandingCommandLineArgumentProvider(
        objects.property("--config-file"),
        scriptConfig.asFileTree
      )
    )
    args(
      "--output-dir", generatedSsh.get()
    )
  }

  // need to add a line like below to ~/.ssh/config
  // Include "/Users/mikekobit/dotfiles/subprojects/shell/ssh/build/generated-ssh/includes"
  dotfiles {
    dependsOn(sshCms, run)
  }
}
