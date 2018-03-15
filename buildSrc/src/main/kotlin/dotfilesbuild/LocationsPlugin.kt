package dotfilesbuild

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.file.Directory

open class LocationsPlugin : Plugin<Project> {
  override fun apply(target: Project) {
    target.run {
      val userHome: String = System.getProperty("user.home")
      providers.provider {  }
      val homeDirectory: Directory = layout.directoryProperty().let {
        it.set(file(userHome))
        it.get()
      }

      val home = LocationsExtension(
          homeDirectory,
          homeDirectory.dir("Workspace"),
          homeDirectory.dir("Programs"),
          homeDirectory.dir("Downloads")
      )

      extensions.add(
          LocationsExtension::class.java,
          "locations",
          home
      )
    }
  }
}
