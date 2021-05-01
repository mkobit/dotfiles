import dotfilesbuild.utilities.home
import org.gradle.api.attributes.Attribute

plugins {
  `lifecycle-base`
  id("dotfilesbuild.dotfiles-lifecycle")
}

val shell = Attribute.of("shell.config", Usage::class.java)

val syncFromHomeFiles by tasks.registering(Sync::class) {
  from(home.dir(".dotfiles/"))
  into(layout.buildDirectory.dir("dotfiles-sync"))
  include("**/**")
}

val syncToHomeFiles by tasks.registering(Sync::class) {
  from(layout.buildDirectory.dir("dotfiles-sync"))
  into(home.dir(".dotfiles/"))
}

val aggregateSshFiles by tasks.registering(Sync::class) {
  from(syncFromHomeFiles)
  into(layout.buildDirectory.dir("shell/ssh"))
  include("**/*.ssh.kts")
}

val aggregateGitFiles by tasks.registering(Sync::class) {
  from(syncFromHomeFiles)
  into(layout.buildDirectory.dir("shell/git"))
  include("**/*.git.kts")
}

configurations {
  val sshConfiguration by creating {
    setupAsOutput(aggregateSshFiles, "ssh")
  }

  val gitConfiguration by creating {
    setupAsOutput(aggregateGitFiles, "git")
  }
}

fun Configuration.setupAsOutput(sync: TaskProvider<Sync>, attributeValue: String) {
  isCanBeConsumed = true
  isCanBeResolved = false
  attributes {
    attribute(shell, objects.named(Usage::class, attributeValue))
  }
  outgoing {
    artifact(sync)
  }
}
