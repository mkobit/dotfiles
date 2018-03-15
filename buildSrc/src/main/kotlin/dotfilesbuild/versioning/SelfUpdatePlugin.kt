package dotfilesbuild.versioning

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.tasks.Exec

open class SelfUpdatePlugin : Plugin<Project> {
  override fun apply(project: Project) {
    project.tasks.create("synchronize", Exec::class.java) {
      description = "Synchronizes the dotfiles source"
      commandLine("dotfilesbuild/io/git", "pull", "--rebase", "--autostash")
      workingDir = project.rootDir
      group = "Self update"
    }
  }
}
