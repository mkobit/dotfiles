import dotfilesbuild.home
import dotfilesbuild.io.file.Mkdir

plugins {
  dotfilesbuild.`dotfiles-lifecycle`
}

tasks {
  val sshCms by registering(Mkdir::class) {
    directory.set(home.dir(".ssh/controlMaster"))
  }

  dotfiles {
    dependsOn(sshCms)
  }
}
