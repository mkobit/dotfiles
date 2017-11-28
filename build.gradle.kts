import org.gradle.api.tasks.Exec
import org.gradle.api.tasks.wrapper.Wrapper

import files.Symlink
import files.Mkdir
import files.WriteFile
import git.CloneRepository
import git.PullRepository
import update.SelfUpdatePlugin

plugins {
  id("com.github.ben-manes.versions") version "0.17.0"
  kotlin("jvm") version "1.2.0" apply false
}

apply {
  plugin<SelfUpdatePlugin>()
  from("gradle/trackedRepositories.gradle.kts")
}

description = "Dotfiles and package management"

val personalWorkspaceDirectory: Directory = homeDir("Workspace/personal")
val workWorkspaceDirectory: Directory = homeDir("Workspace/work")
val codeLabWorkspaceDirectory: Directory = homeDir("Workspace/code_lab")

tasks {
  val personalWorkspace by creating(Mkdir::class) {
    directoryProvider = personalWorkspaceDirectory
  }

  val workWorkspace by creating(Mkdir::class) {
    directoryProvider = workWorkspaceDirectory
  }

  val codeLabWorkspace by creating(Mkdir::class) {
    directoryProvider = codeLabWorkspaceDirectory
  }

  val workspace by creating {
    group = "Workspace"
    dependsOn(personalWorkspace, workWorkspace, codeLabWorkspace)
  }

  val gitConfigGeneration by creating(WriteFile::class) {
    val gitConfigGeneral = projectFile("git/gitconfig_general.dotfile")
    val gitConfigPersonal = projectFile("git/gitconfig_personal.dotfile")
    inputs.files(gitConfigGeneral, gitConfigPersonal)
    textState.set(provider {
      """[include]
    path = ${gitConfigGeneral.asFile.absolutePath}
[includeIf "gitdir:${project.rootDir.absolutePath}/"]
    path = ${gitConfigPersonal.asFile.absolutePath}
[includeIf "gitdir:${personalWorkspace.directory!!.absolutePath}/"]
    path = ${gitConfigPersonal.asFile.absolutePath}
[includeIf "gitdir:${codeLabWorkspace.directory!!.absolutePath}/"]
    path = ${gitConfigPersonal.asFile.absolutePath}
[includeIf "gitdir:${workWorkspace.directory!!.absolutePath}/"]
    path = ${homeFile(".gitconfig_work")}
"""
    })
    destinationProvider = homeFile(".gitconfig")
    dependsOn(workspace)
  }

  val gitIgnoreGlobal by creating(Symlink::class) {
    sourceProvider = projectFile("git/gitignore_global.dotfile")
    destinationProvider = homeFile(".gitignore_global")
  }

  val git by creating {
    group = "Git"
    dependsOn(gitConfigGeneration, gitIgnoreGlobal)
  }

  val screenRc by creating(Symlink::class) {
    sourceProvider = projectFile("screen/screenrc.dotfile")
    destinationProvider = homeFile(".screenrc")
  }

  val screen by creating {
    group = "Screen"
    dependsOn(screenRc)
  }

  val tmuxConf by creating(Symlink::class) {
    sourceProvider = projectFile("tmux/tmux.conf.dotfile")
    destinationProvider = homeFile(".tmux.conf")
  }

  val sshCms by creating(Mkdir::class) {
    directoryProvider = homeDir(".ssh/controlMaster")
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
    sourceProvider = projectFile("vim/vimrc.dotfile")
    destinationProvider = homeFile(".vimrc")
  }

  val vim by creating {
    group = "VIM"
    dependsOn(vimRc)
  }

  "wrapper"(Wrapper::class) {
    gradleVersion = "4.4-rc-4"
    distributionType = Wrapper.DistributionType.ALL
  }

  "dotfiles" {
    description = "Sets up all dotfiles and packages"
    group = "Install"
    dependsOn(git, screen, ssh, tmux, vim, workspace)
  }
}

// TODO: move all of this into some extension or buildSrc managed plugin
val trackedRepositories: Map<String, List<String>> by extra
val cloneAllTrackedRepositories by tasks.creating {
  description = "Clones all tracked repositories"
  group = "Repository Management"
}
val pullAllTrackedRepositories by tasks.creating {
  description = "Pulls all tracked repositories"
  group = "Repository Management"
}
trackedRepositories.forEach { grouping, urls ->
  val repositoryGroupingDirectory: Directory = personalWorkspaceDirectory.dir(grouping)
  val groupingTask = tasks.create("clone${grouping.capitalize()}RepositoryGroup", Mkdir::class.java) {
    directoryProvider = repositoryGroupingDirectory
  }
  urls.forEach { url ->
    val repositoryName = url.run {
      val ofGit = lastIndexOf(".git").let {
        if (it > 0) {
          it
        } else {
          length
        }
      }
      val ofSlash = lastIndexOf("/")
      substring(ofSlash + 1, ofGit)
    }
    val repositoryDirectory = repositoryGroupingDirectory.dir(repositoryName)
    val cloneTask = tasks.create("clone${grouping.capitalize()}Repository$repositoryName", CloneRepository::class.java) {
      dependsOn(groupingTask)
      repositoryDirectoryProvider = repositoryDirectory
      repositoryUrlState.set(url)
    }
    cloneAllTrackedRepositories.dependsOn(cloneTask)

    val syncTask = tasks.create("pull${grouping.capitalize()}Repository$repositoryName", PullRepository::class.java) {
      dependsOn(cloneTask)
      repositoryDirectoryProvider = repositoryDirectory
    }
    pullAllTrackedRepositories.dependsOn(syncTask)
  }
}
