package dotfilesbuild.shell

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.plugins.BasePlugin
import org.gradle.kotlin.dsl.apply

class SourceControlledBinPlugin : Plugin<Project> {
  override fun apply(target: Project) {
    target.run {
      apply<GeneratedZshrcSourceFilePlugin>()
      apply<BasePlugin>()
    }
  }
}
