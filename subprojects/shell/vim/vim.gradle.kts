import dotfilesbuild.homeFile
import dotfilesbuild.projectFile
import dotfilesbuild.io.file.Symlink

plugins {
  dotfilesbuild.`dotfiles-lifecycle`
}

tasks {
  val symlinkVimrcConf by registering(Symlink::class) {
    source.set(projectFile("config/vimrc.dotfile"))
    destination.set(homeFile(".vimrc"))
  }

  dotfiles {
    dependsOn(symlinkVimrcConf)
  }
}
