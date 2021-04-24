import dotfilesbuild.utilities.home
import dotfilesbuild.utilities.projectFile
import dotfilesbuild.io.file.Symlink

plugins {
  id("dotfilesbuild.dotfiles-lifecycle")
  id("dotfilesbuild.io.noop")
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
