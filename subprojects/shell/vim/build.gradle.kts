plugins {
  id("dotfilesbuild.dotfiles-lifecycle")
}

tasks {
  val stageVimFiles by registering(Sync::class) {
    from(layout.projectDirectory.dir("config"))
    into(layout.buildDirectory.dir("generated-vim-config-staging"))
  }

  val syncStaged by registering(Sync::class) {
    from(stageVimFiles)
    into(layout.buildDirectory.dir("generated-vim-config"))
  }

  dotfiles {
    // add directive to ~/.vimrc to vim file
    // :source <path>
    dependsOn(syncStaged)
  }
}
