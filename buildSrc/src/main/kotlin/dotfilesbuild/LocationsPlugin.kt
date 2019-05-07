package dotfilesbuild

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.file.Directory
import org.gradle.api.model.ObjectFactory
import org.gradle.kotlin.dsl.add
import javax.inject.Inject

class LocationsPlugin @Inject constructor(private val objectFactory: ObjectFactory) : Plugin<Project> {
  override fun apply(target: Project) {
    target.run {
      val userHome: String = System.getProperty("user.home")
      val homeDirectory: Directory = objectFactory.directoryProperty().let {
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
          LocationsExtension::class,
          "locations",
          home
      )
    }
  }
}
