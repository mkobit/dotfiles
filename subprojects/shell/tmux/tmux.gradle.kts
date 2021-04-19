import dotfilesbuild.home
import dotfilesbuild.projectFile
import dotfilesbuild.io.file.Symlink

plugins {
  id("dotfilesbuild.dotfiles-lifecycle")
}

tasks {
  val symlinkTmuxConf by registering(Symlink::class) {
    source.set(projectFile("config/tmux.conf.dotfile"))
    destination.set(home.file(".tmux.conf"))
  }

  dotfiles {
    dependsOn(symlinkTmuxConf)
  }
}
