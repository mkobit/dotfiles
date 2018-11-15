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
import org.gradle.kotlin.dsl.provideDelegate
import org.gradle.kotlin.dsl.registering

class UnmanagedBinPlugin : Plugin<Project> {

  companion object {
    private const val COMMENT = "# dotfiles: dotfiles unmanaged bin files"
  }

  override fun apply(target: Project) {
    target.run {
      apply<BasePlugin>()
      apply<GeneratedZshrcSourceFilePlugin>()
      val makeUnmanagedBinDirectory by tasks.registering(Mkdir::class) {
        description = "Creates the unmanaged bin directory that can be included on the PATH"
        directory.set(target.layout.projectDirectory.dir(".unmanaged_bin"))
      }

      val generateZshrcFile by tasks.existing(EditFile::class) {
        dependsOn(makeUnmanagedBinDirectory)
        val managedBinDirectory = makeUnmanagedBinDirectory
            .flatMap { it.directory }
            .map { it.asFile }
            .map { it.absolutePath }
        editActions.add(
            ReplaceText(
                Regex("export PATH=.*\\s+${COMMENT}"),
                true
            ) {
              "export PATH=\"\$PATH:${managedBinDirectory.get()}\" ${COMMENT}"
            }
        )
      }
    }
  }
}
