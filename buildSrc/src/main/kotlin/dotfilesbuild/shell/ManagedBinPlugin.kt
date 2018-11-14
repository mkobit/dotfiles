// needed for kotlin-dsl imports right now as they don't automatically
@file:Suppress("UnusedImport")
package dotfilesbuild.shell

import dotfilesbuild.io.file.Mkdir
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.plugins.BasePlugin
import org.gradle.api.tasks.Delete
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.getValue
import org.gradle.kotlin.dsl.named
import org.gradle.kotlin.dsl.provideDelegate
import org.gradle.kotlin.dsl.registering

class ManagedBinPlugin : Plugin<Project> {
  override fun apply(target: Project) {
    target.run {
      apply<GeneratedZshrcSourceFilePlugin>()
      apply<BasePlugin>()
      val makeManagedBinDirectory by tasks.registering(Mkdir::class) {
        description = "Creates the managed bin directory that can be included on the PATH"
        directory.set(target.layout.buildDirectory.dir("managed_bin"))
      }
    }
  }
}
