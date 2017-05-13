import org.gradle.api.tasks.Exec
import org.gradle.api.tasks.wrapper.Wrapper

import files.Symlink

description = "Dotfiles and package management of laptop"

tasks {
  val synchronize by creating(Exec::class) {
    commandLine("git", "pull", "--rebase", "--autostash")
    setWorkingDir(project.rootDir)
  }
  val gitIgnoreGlobal by creating(Symlink::class) {
    source = projectFile("git/gitignore_global.dotfile")
    destination = homeFile(".gitignore_global")
  }
  val git by creating {
    group = "Git"
    dependsOn(gitIgnoreGlobal)
  }

  val screenRc by creating(Symlink::class) {
    source = projectFile("screen/screenrc.dotfile")
    destination = homeFile(".screenrc")
  }

  val screen by creating {
    group = "Screen"
    dependsOn(screenRc)
  }

  val tmuxConf by creating(Symlink::class) {
    source = projectFile("tmux/tmux.conf.dotfile")
    destination = homeFile(".tmux.conf")
  }

  val tmux by creating {
    group = "Tmux"
    dependsOn(tmuxConf)
  }

  val vimRc by creating(Symlink::class) {
    source = projectFile("vim/vimrc.dotfile")
    destination = homeFile(".vimrc")
  }

  val vim by creating {
    group = "VIM"
    dependsOn(vimRc)
  }

  "dotfiles" {
    description = "Sets up all dotfiles and packages"
    group = "Install"
    dependsOn(git, screen, tmux, vim)
  }

  "wrapper"(Wrapper::class) {
    gradleVersion = "3.5"
  }

  project.defaultTasks(synchronize.name)
}
