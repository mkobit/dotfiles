// needed for kotlin-dsl imports right now as they don't automatically
@file:Suppress("UnusedImport")
package dotfilesbuild.shell

import dotfilesbuild.io.file.EditFile
import dotfilesbuild.io.file.Mkdir
import dotfilesbuild.io.file.content.ReplaceText
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.plugins.BasePlugin
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.existing
import org.gradle.kotlin.dsl.getValue
import org.gradle.kotlin.dsl.registering

/**
 * Contains binaries downloaded and managed by this project.
 */
class ManagedBinPlugin : Plugin<Project> {
  companion object {
    private const val COMMENT = "# dotfiles: dotfiles managed bin files"
  }

  override fun apply(target: Project) {
    target.run {
      apply<GeneratedZshrcSourceFilePlugin>()
      apply<BasePlugin>()
      val makeManagedBinDirectory by tasks.registering(Mkdir::class) {
        description = "Creates the managed bin directory that can be included on the PATH"
        directory.set(target.layout.buildDirectory.dir("managed_bin"))
      }

      val generateZshrcFile by tasks.existing(EditFile::class) {
        dependsOn(makeManagedBinDirectory)
        val managedBinDirectory = makeManagedBinDirectory
            .flatMap { it.directory }
            .map { it.asFile }
            .map { it.absolutePath }
        editActions.add(
            ReplaceText(
                Regex("export PATH=.*\\s+$COMMENT"),
                true
            ) {
              "export PATH=\"\$PATH:${managedBinDirectory.get()}\" $COMMENT"
            }
        )
      }
    }
  }
}
