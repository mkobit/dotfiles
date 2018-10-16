package dotfilesbuild.keepass

import dotfilesbuild.LocationsExtension
import dotfilesbuild.LocationsPlugin
import dotfilesbuild.io.file.Symlink
import dotfilesbuild.io.http.Download
import mu.KotlinLogging
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.tasks.Copy
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.create
import org.gradle.kotlin.dsl.getByType
import org.gradle.kotlin.dsl.property
import org.gradle.kotlin.dsl.register
import java.util.concurrent.Callable

open class KeepassProgramPlugin : Plugin<Project> {

  companion object {
    private val log = KotlinLogging.logger { }
    private const val TASK_GROUP = "KeePass"
  }

  override fun apply(target: Project) {
    target.run {
      apply<LocationsPlugin>()

      val locations = extensions.getByType(LocationsExtension::class)
      val keepass = extensions.create(
          "keepass",
          KeepassExtension::class,
          objects.property<String>(),
          layout.directoryProperty().apply {
            set(locations.downloads)
          },
          layout.directoryProperty().apply {
            set(locations.programs)
          }
      )
      val downloadKeepassZip = tasks.register("downloadKeepassZip", Download::class) {
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
      val extractKeepassZip = tasks.register("extractKeepassZip", Copy::class) {
        description = "Extracts the KeePass ZIP distribution"
        group = TASK_GROUP
        dependsOn(downloadKeepassZip)
        from(Callable { zipTree(downloadKeepassZip.map(Download::destination).get()) })
        into(installDirectoryForVersion)
      }
      tasks.register("symlinkKeePassProgram", Symlink::class) {
        description = "Creates a symlink to the KeePass directory"
        group = TASK_GROUP
        dependsOn(extractKeepassZip)
        source.set(installDirectoryForVersion)
        destination.set(keepass.installDirectory.dir("keepass"))
      }
    }
  }
}
