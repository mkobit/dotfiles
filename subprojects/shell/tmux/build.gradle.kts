plugins {
  id("dotfilesbuild.dotfiles-lifecycle")
}

tasks {
  val stageTmuxFiles by registering(Sync::class) {
    from(layout.projectDirectory.dir("config"))
    into(layout.buildDirectory.dir("generated-tmux-config-staging"))
  }

  val syncStaged by registering(Sync::class) {
    from(stageTmuxFiles)
    into(layout.buildDirectory.dir("generated-tmux-config"))
  }

  dotfiles {
    // add directive to ~/.tmux.conf tmux configuration file
    // source-file <path>
    dependsOn(syncStaged)
  }
}
