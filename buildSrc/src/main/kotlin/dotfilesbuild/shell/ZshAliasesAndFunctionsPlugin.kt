package dotfilesbuild.shell

import dotfilesbuild.io.file.EditFile
import dotfilesbuild.io.file.content.ReplaceText
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.plugins.BasePlugin
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.existing
import org.gradle.kotlin.dsl.getValue
import org.gradle.kotlin.dsl.provideDelegate // ktlint-disable no-unused-imports

class ZshAliasesAndFunctionsPlugin : Plugin<Project> {

  companion object {
    private const val ALIASES_COMMENT = "# dotfiles: aliases.source"
    private const val FUNCTIONS_COMMENT = "# dotfiles: functions.source"
  }

  override fun apply(target: Project) {
    target.run {
      apply<GeneratedZshrcSourceFilePlugin>()
      apply<BasePlugin>()
      val generateZshrcFile by tasks.existing(EditFile::class) {
        editActions.add(
            ReplaceText(
                Regex("\\. .*\\s+$ALIASES_COMMENT"),
                true
            ) {
              ". \"${file("zsh/aliases.source").absolutePath}\" $ALIASES_COMMENT"
            }
        )
        editActions.add(
            ReplaceText(
                Regex("\\. .*\\s+$FUNCTIONS_COMMENT"),
                true
            ) {
              ". \"${file("zsh/functions.source").absolutePath}\" $FUNCTIONS_COMMENT"
            }
        )
      }
    }
  }
}
