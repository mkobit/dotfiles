// needed for kotlin-dsl imports right now as they don't automatically
@file:Suppress("UnusedImport")
package dotfilesbuild.shell

import dotfilesbuild.io.file.EditFile
import dotfilesbuild.io.file.content.ReplaceText
import dotfilesbuild.io.file.content.SearchTextReplaceLine
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.plugins.BasePlugin
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.existing
import org.gradle.kotlin.dsl.getValue
import org.gradle.kotlin.dsl.provideDelegate

class SourceControlledBinPlugin : Plugin<Project> {
  companion object {
    private const val COMMENT = "# dotfiles: source controlled bin files"
  }

  override fun apply(target: Project) {
    target.run {
      apply<GeneratedZshrcSourceFilePlugin>()
      apply<BasePlugin>()

      val generateZshrcFile by tasks.existing(EditFile::class) {
        val sourceControlledBinDir = target.layout.projectDirectory.dir("bin").asFile.absolutePath
        editActions.add(
            ReplaceText(
                Regex("export PATH=.*\\s+$COMMENT"),
                true
            ) {
              "export PATH=\"\$PATH:${sourceControlledBinDir}\" $COMMENT"
            }
        )
      }
    }
  }
}
