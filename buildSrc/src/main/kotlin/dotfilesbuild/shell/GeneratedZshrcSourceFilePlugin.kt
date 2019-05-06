// needed for kotlin-dsl imports right now as they don't automatically
@file:Suppress("UnusedImport")
package dotfilesbuild.shell

import dotfilesbuild.io.file.EditFile
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.plugins.BasePlugin
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.get
import org.gradle.kotlin.dsl.getValue
import org.gradle.kotlin.dsl.registering

class GeneratedZshrcSourceFilePlugin : Plugin<Project> {
  companion object {
    private const val ZSHRC_GROUP = "Zsh"
  }
  override fun apply(target: Project) {
    target.run {
      apply<BasePlugin>()
      val generateZshrcFile by tasks.registering(EditFile::class) {
        group = ZSHRC_GROUP
        description = "Generates a ZSH file than be sourced that only contains dotfiles specific content"
        file.set(layout.buildDirectory.file("zsh/generated_zshrc"))
        doLast("display location of file") {
          logger.lifecycle("Location of generated source file is ${file.get().asFile}")
        }
      }
    }
  }
}
