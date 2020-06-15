import dotfilesbuild.home
import dotfilesbuild.projectFile
import dotfilesbuild.io.file.EditFile
import dotfilesbuild.io.file.Symlink
import dotfilesbuild.io.file.content.SetContent

plugins {
  dotfilesbuild.`dotfiles-lifecycle`
}

val workspace = home.dir("Workspace")
val personalWorkspaceDirectory: Directory = workspace.dir("personal")
val workWorkspaceDirectory: Directory = workspace.dir("work")
val codeLabWorkspaceDirectory: Directory = workspace.dir("code_lab")

tasks {
  val gitConfigGeneration by registering(EditFile::class) {
    val gitConfigGeneral = projectFile("gitconfig/gitconfig_general.dotfile")
    val gitConfigPersonal = projectFile("gitconfig/gitconfig_personal.dotfile")
    editActions.set(listOf(
      SetContent {
        """
                [include]
                    path = ${gitConfigGeneral.asFile.absolutePath}
                [includeIf "gitdir:${home.dir("dotfiles").asFile.absolutePath}/"]
                    path = ${gitConfigPersonal.asFile.absolutePath}
                [includeIf "gitdir:${project.rootDir.absolutePath}/"]
                    path = ${gitConfigPersonal.asFile.absolutePath}
                [includeIf "gitdir:${personalWorkspaceDirectory.asFile.absolutePath}/"]
                    path = ${gitConfigPersonal.asFile.absolutePath}
                [includeIf "gitdir:${codeLabWorkspaceDirectory.asFile.absolutePath}/"]
                    path = ${gitConfigPersonal.asFile.absolutePath}
                [includeIf "gitdir:${workWorkspaceDirectory.asFile.absolutePath}/"]
                    path = ${home.file(".gitconfig_work").asFile.absolutePath}
            """.trimIndent()
      }
    ))
    file.set(layout.buildDirectory.file("generated/.gitconfig"))
  }

  val symlinkGeneratedGitFile  by registering(Symlink::class) {
    dependsOn(gitConfigGeneration)
    source.set(gitConfigGeneration.flatMap { it.output })
    destination.set(home.file(".gitconfig"))
  }

  val symlinkGitIgnoreGlobal by registering(Symlink::class) {
    source.set(projectFile("git/gitignore_global.dotfile"))
    destination.set(home.file(".gitignore_global"))
  }

  dotfiles {
    dependsOn(symlinkGeneratedGitFile, symlinkGitIgnoreGlobal)
  }
}
