import dotfilesbuild.utilities.home
import org.gradle.api.attributes.Attribute

plugins {
  `lifecycle-base`
  // id("org.jlleitschuh.gradle.ktlint")
  id("dotfilesbuild.dotfiles-lifecycle")
}

val shell = Attribute.of("shell.config", Usage::class.java)

val syncHomeFiles by tasks.registering(Sync::class) {
  from(home.dir(".dotfiles/"))
  into(layout.buildDirectory.dir("dotfiles-sync"))
  include("**/**")
}

val aggregateSshFiles by tasks.registering(Sync::class) {
  from(syncHomeFiles)
  into(layout.buildDirectory.dir("shell/ssh"))
  include("**/*.hocon")
  include {
    it.name.contains("ssh") || it.path.contains("ssh")
  }
}

val aggregateGitFiles by tasks.registering(Sync::class) {
  from(syncHomeFiles)
  into(layout.buildDirectory.dir("shell/git"))
  include("**/*.hocon")
  include {
    it.name.contains("git") || it.path.contains("git")
  }
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
