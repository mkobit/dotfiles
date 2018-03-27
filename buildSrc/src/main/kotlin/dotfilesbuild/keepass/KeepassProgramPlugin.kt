package dotfilesbuild.keepass

import dotfilesbuild.LocationsExtension
import dotfilesbuild.LocationsPlugin
import dotfilesbuild.io.file.SymlinkDirectory
import dotfilesbuild.io.http.Download
import mu.KotlinLogging
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.tasks.Copy
import org.gradle.kotlin.dsl.property
import java.util.concurrent.Callable

open class KeepassProgramPlugin : Plugin<Project> {

  companion object {
    private val log = KotlinLogging.logger { }
    private const val TASK_GROUP = "KeePass"
  }

  override fun apply(target: Project) {
    target.run {
      pluginManager.apply(LocationsPlugin::class.java)

      val locations = extensions.findByType(LocationsExtension::class.java)!!
      val keepass = extensions.create(
          "keepass",
          KeepassExtension::class.java,
          objects.property<String>(),
          layout.directoryProperty().apply {
            set(locations.downloads)
          },
          layout.directoryProperty().apply {
            set(locations.programs)
          }
      )
      val downloadKeepassZip = tasks.create("downloadKeepassZip", Download::class.java) {
        description = "Downloads the KeePass ZIP distribution"
        group = TASK_GROUP
        destination.set(
            keepass.downloadDirectory.file(keepass.keepassVersion.map { version -> "KeePass-$version.zip" })
        )
        url.set(keepass.keepassVersion.map { version ->
          "https://sourceforge.net/projects/keepass/files/KeePass ${version[0]}.x/$version/KeePass-$version.zip/download"
        })
      }
      val installDirectoryForVersion = keepass.installDirectory.dir(keepass.keepassVersion.map { "KeePass-$it" })
      val extractKeepassZip = tasks.create("extractKeepassZip", Copy::class.java) {
        description = "Extracts the KeePass ZIP distribution"
        group = TASK_GROUP
        dependsOn(downloadKeepassZip)
        from(Callable { zipTree(downloadKeepassZip.destination) })
        into(installDirectoryForVersion)
      }
      val symlinkKeePassProgram = tasks.create("symlinkKeePassProgram", SymlinkDirectory::class.java) {
        description = "Creates a symlink to the KeePass directory"
        group = TASK_GROUP
        dependsOn(extractKeepassZip)
        source.set(installDirectoryForVersion)
        destination.set(keepass.installDirectory.dir("keepass"))
      }
    }
  }
}
