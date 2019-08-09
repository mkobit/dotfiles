import dotfilesbuild.projectFile
import dotfilesbuild.io.file.EditFile
import dotfilesbuild.io.file.Symlink
import dotfilesbuild.io.file.content.SetContent

plugins {
  dotfilesbuild.`dotfiles-lifecycle`

  dotfilesbuild.locations
}

val personalWorkspaceDirectory: Directory = locations.workspace.dir("personal")
val workWorkspaceDirectory: Directory = locations.workspace.dir("work")
val codeLabWorkspaceDirectory: Directory = locations.workspace.dir("code_lab")

tasks {
  val gitConfigGeneration by registering(EditFile::class) {
    val gitConfigGeneral = projectFile("gitconfig/gitconfig_general.dotfile")
    val gitConfigPersonal = projectFile("gitconfig/gitconfig_personal.dotfile")
    editActions.set(listOf(
      SetContent {
        """
                [include]
                    path = ${gitConfigGeneral.asFile.absolutePath}
                [includeIf "gitdir:${project.rootDir.absolutePath}/"]
                    path = ${gitConfigPersonal.asFile.absolutePath}
                [includeIf "gitdir:${personalWorkspaceDirectory.asFile.absolutePath}/"]
                    path = ${gitConfigPersonal.asFile.absolutePath}
                [includeIf "gitdir:${codeLabWorkspaceDirectory.asFile.absolutePath}/"]
                    path = ${gitConfigPersonal.asFile.absolutePath}
                [includeIf "gitdir:${workWorkspaceDirectory.asFile.absolutePath}/"]
                    path = ${locations.home.file(".gitconfig_work")}
            """.trimIndent()
      }
    ))
    file.set(layout.buildDirectory.file("generated/.gitconfig"))
  }

  val symlinkGeneratedGitFile  by registering(Symlink::class) {
    dependsOn(gitConfigGeneration)
    source.set(gitConfigGeneration.flatMap { it.output })
    destination.set(locations.home.file(".gitconfig"))
  }

  val symlinkGitIgnoreGlobal by registering(Symlink::class) {
    source.set(projectFile("git/gitignore_global.dotfile"))
    destination.set(locations.home.file(".gitignore_global"))
  }

  dotfiles {
    dependsOn(symlinkGeneratedGitFile, symlinkGitIgnoreGlobal)
  }
}
