import org.gradle.api.tasks.Exec
import org.gradle.api.tasks.wrapper.Wrapper
import dotfilesbuild.io.file.Symlink
import dotfilesbuild.io.file.Mkdir
import dotfilesbuild.io.file.WriteFile
import dotfilesbuild.io.git.CloneRepository
import dotfilesbuild.io.git.PullRepository

plugins {
  id("com.github.ben-manes.versions") version "0.17.0"
  kotlin("jvm") version "1.2.30" apply false

  id("dotfilesbuild.self-update")
  id("dotfilesbuild.locations")
}

apply {
  from("gradle/trackedRepositories.gradle.kts")
}

description = "Dotfiles and package management"

val personalWorkspaceDirectory: Directory = locations.workspace.dir("personal")
val workWorkspaceDirectory: Directory = locations.workspace.dir("work")
val codeLabWorkspaceDirectory: Directory = locations.workspace.dir("code_lab")

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
      """
        [include]
            path = ${gitConfigGeneral.asFile.absolutePath}
        [includeIf "gitdir:${project.rootDir.absolutePath}/"]
            path = ${gitConfigPersonal.asFile.absolutePath}
        [includeIf "gitdir:${personalWorkspace.directory!!.absolutePath}/"]
            path = ${gitConfigPersonal.asFile.absolutePath}
        [includeIf "gitdir:${codeLabWorkspace.directory!!.absolutePath}/"]
            path = ${gitConfigPersonal.asFile.absolutePath}
        [includeIf "gitdir:${workWorkspace.directory!!.absolutePath}/"]
            path = ${locations.home.file(".gitconfig_work")}
      """.trimIndent()
    })
    destinationProvider = locations.home.file(".gitconfig")
    dependsOn(workspace)
  }

  val gitIgnoreGlobal by creating(Symlink::class) {
    sourceProvider = projectFile("git/gitignore_global.dotfile")
    destinationProvider = locations.home.file(".gitignore_global")
  }

  val git by creating {
    group = "Git"
    dependsOn(gitConfigGeneration, gitIgnoreGlobal)
  }

  val screenRc by creating(Symlink::class) {
    sourceProvider = projectFile("screen/screenrc.dotfile")
    destinationProvider = locations.home.file(".screenrc")
  }

  val screen by creating {
    group = "Screen"
    dependsOn(screenRc)
  }

  val tmuxConf by creating(Symlink::class) {
    sourceProvider = projectFile("tmux/tmux.conf.dotfile")
    destinationProvider = locations.home.file(".tmux.conf")
  }

  val sshCms by creating(Mkdir::class) {
    directoryProvider = locations.home.dir(".ssh/controlMaster")
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
    destinationProvider = locations.home.file(".vimrc")
  }

  val vim by creating {
    group = "VIM"
    dependsOn(vimRc)
  }

  "wrapper"(Wrapper::class) {
    gradleVersion = "4.6"
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
