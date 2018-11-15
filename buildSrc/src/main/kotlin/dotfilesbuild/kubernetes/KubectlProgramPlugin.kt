// needed for kotlin-dsl imports right now as they don't automatically
@file:Suppress("UnusedImport")
package dotfilesbuild.kubernetes

import dotfilesbuild.io.file.Mkdir
import dotfilesbuild.io.http.Download
import dotfilesbuild.shell.ManagedBinPlugin
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.file.Directory
import org.gradle.api.provider.Provider
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.create
import org.gradle.kotlin.dsl.existing
import org.gradle.kotlin.dsl.getValue
import org.gradle.kotlin.dsl.provideDelegate
import org.gradle.kotlin.dsl.registering
import org.gradle.kotlin.dsl.newInstance
import org.gradle.kotlin.dsl.property

class KubectlProgramPlugin : Plugin<Project> {
  override fun apply(target: Project) {
    target.run {
      // TODO: this plugin should not need as much explicit information about the plugin it is building on top of.
      // Instead, introduce another layer or helper base plugin to make this kind of shared capability.
      apply<ManagedBinPlugin>()
      val makeManagedBinDirectory by tasks.existing(Mkdir::class)
      val kubectl = extensions.create<KubectlProgramExtension>("kubectl", objects.property<String>())
      val downloadKubeCtl by tasks.registering(Download::class) {
        description = "Download kubectl and make it executable"
        url.set(
            kubectl.version.map {
              "https://storage.googleapis.com/kubernetes-release/release/$it/bin/darwin/amd64/kubectl" // TODO: determine arch before download
            }
        )
        destination.set(
            makeManagedBinDirectory
                .flatMap { it.directory }
                .map { it.file("kubectl") }
        )
        executable.set(true)
      }
    }
  }
}
