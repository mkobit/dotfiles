import org.gradle.api.tasks.Exec
import org.gradle.api.tasks.wrapper.Wrapper

import files.Symlink
import files.Mkdir
import files.WriteFile

description = "Dotfiles and package management"

tasks {
  val personalWorkspace by creating(Mkdir::class) {
    directory = homeFile("Workspace/personal")
  }

  val workWorkspace by creating(Mkdir::class) {
    directory = homeFile("Workspace/work")
  }

  val codeLabWorkspace by creating(Mkdir::class) {
    directory = homeFile("Workspace/code_lab")
  }

  val workspace by creating {
    group = "Workspace"
    dependsOn(personalWorkspace, workWorkspace, codeLabWorkspace)
  }

  val synchronize by creating(Exec::class) {
    commandLine("git", "pull", "--rebase", "--autostash")
    setWorkingDir(project.rootDir)
  }

  val gitConfigGeneration by creating(WriteFile::class) {
    val gitConfigGeneral = projectFile("git/gitconfig_general.dotfile")
    val gitConfigPersonal = projectFile("git/gitconfig_personal.dotfile")
    inputs.files(gitConfigGeneral, gitConfigPersonal)
    text = """[include]
    path = ${gitConfigGeneral.absolutePath}
[includeIf "gitdir:${project.rootDir.absolutePath}/"]
    path = ${gitConfigPersonal.absolutePath}
[includeIf "gitdir:${personalWorkspace.directory!!.absolutePath}/"]
    path = ${gitConfigPersonal.absolutePath}
[includeIf "gitdir:${codeLabWorkspace.directory!!.absolutePath}/"]
    path = ${gitConfigPersonal.absolutePath}
[includeIf "gitdir:${workWorkspace.directory!!.absolutePath}/"]
    path = ${homeFile(".gitconfig_work")}
"""
    destination = homeFile(".gitconfig")
    dependsOn(workspace)
  }

  val gitIgnoreGlobal by creating(Symlink::class) {
    source = projectFile("git/gitignore_global.dotfile")
    destination = homeFile(".gitignore_global")
  }

  val git by creating {
    group = "Git"
    dependsOn(gitConfigGeneration, gitIgnoreGlobal)
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

  val sshCms by creating(Mkdir::class) {
    directory = homeFile(".ssh/controlMaster")
  }

  val ssh by creating {
    group = "SSH"
    dependsOn(sshCms)
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

  "wrapper"(Wrapper::class) {
    gradleVersion = "4.1"
    distributionType = Wrapper.DistributionType.ALL
  }

  "dotfiles" {
    description = "Sets up all dotfiles and packages"
    group = "Install"
    dependsOn(git, screen, ssh, tmux, vim, workspace)
  }

  project.defaultTasks(synchronize.name)
}
