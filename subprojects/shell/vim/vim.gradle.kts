import dotfilesbuild.home
import dotfilesbuild.projectFile
import dotfilesbuild.io.file.Symlink

plugins {
  id("dotfilesbuild.dotfiles-lifecycle")
}

tasks {
  val symlinkVimrcConf by registering(Symlink::class) {
    source.set(projectFile("config/vimrc.dotfile"))
    destination.set(home.file(".vimrc"))
  }

  dotfiles {
    dependsOn(symlinkVimrcConf)
  }
}
