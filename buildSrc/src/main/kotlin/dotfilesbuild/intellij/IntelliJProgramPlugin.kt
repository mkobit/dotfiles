package dotfilesbuild.intellij

import dotfilesbuild.LocationsExtension
import dotfilesbuild.LocationsPlugin
import dotfilesbuild.io.http.Download
import mu.KotlinLogging
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.tasks.Copy
import org.gradle.kotlin.dsl.property
import java.util.concurrent.Callable

open class IntelliJProgramPlugin : Plugin<Project> {

  companion object {
    private val log = KotlinLogging.logger { }
    private const val TASK_GROUP = "KeePass"
  }

  override fun apply(target: Project) {
    target.run {
      pluginManager.apply(LocationsPlugin::class.java)

      val locations = extensions.findByType(LocationsExtension::class.java)!!
      val intellij = extensions.create(
          "intellij",
          IntelliJExtension::class.java,
          objects.property<String>(),
          objects.property<Distribution>().apply {
            set(Distribution.ULTIMATE)
          },
          layout.directoryProperty().apply {
            set(locations.downloads)
          },
          layout.directoryProperty().apply {
            set(locations.programs)
          }
      )
      val downloadIntellijZip = tasks.create("downloadIntellijZip", Download::class.java) {
        description = "Downloads the IntelliJ ZIP distribution"
        group = TASK_GROUP
        destination.set(
            intellij.downloadDirectory.file(intellij.intellijVersion.map { version ->
              intellij.distributionType.map { type ->
                "https://download.jetbrains.com/idea/idea${type.code}-$version.tar.gz"
                "idea${type.code}-$version.tar.gz"
              }
            }.map { it.get() })
        )
        url.set(intellij.intellijVersion.map { version ->
          intellij.distributionType.map { type ->
            "https://download.jetbrains.com/idea/idea${type.code}-$version.tar.gz"
          }
        }.map { it.get() })
      }
      // TODO: never up to date for some stupid reason
      val extractIntellijZip = tasks.create("extractIntellijZip", Copy::class.java) {
        description = "Extracts the IntelliJ ZIP distribution"
        group = TASK_GROUP
        dependsOn(downloadIntellijZip)
        from(Callable { tarTree(downloadIntellijZip.destination) })
        into(intellij.installDirectory)
      }
      // TODO: figure out how to get the actual top-level dir of the extracted program and symlink it
      // TODO: SymlinkDirectory seems to create output directory even when we want it to be a symlink so need to fix that
//      val symlinkIntellijProgram = tasks.create("symlinkIntellijProgram", SymlinkDirectory::class.java) {
//        description = "Creates a symlink to the IntelliJ directory"
//        group = TASK_GROUP
//        dependsOn(extractIntellijZip)
//        source.set(intellij.installDirectory.dir(provider {
//          println("tar first name: ${tarTree(downloadIntellijZip.destination).first().name}")
//          tarTree(downloadIntellijZip.destination).first().name
//        }))
////        destination.set(intellij.installDirectory.dir("intellij"))
//        destination.set(layout.buildDirectory.dir("intellij"))
//      }
    }
  }
}
