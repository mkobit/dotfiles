// needed for kotlin-dsl imports right now as they don't automatically
@file:Suppress("UnusedImport")
package dotfilesbuild.shell

import dotfilesbuild.io.file.Mkdir
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.plugins.BasePlugin
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.getValue
import org.gradle.kotlin.dsl.provideDelegate
import org.gradle.kotlin.dsl.registering

class UnmanagedBinPlugin : Plugin<Project> {
  override fun apply(target: Project) {
    target.run {
      apply<BasePlugin>()
      apply<GeneratedZshrcSourceFilePlugin>()
      val makeUnmanagedBinDirectory by tasks.registering(Mkdir::class) {
        description = "Creates the unmanaged bin directory that can be included on the PATH"
        directory.set(target.layout.projectDirectory.dir(".unmanaged_bin"))
      }
    }
  }
}
