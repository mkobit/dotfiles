package dotfilesbuild.config

import org.gradle.api.GradleException
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.create
import org.gradle.kotlin.dsl.listProperty
import java.nio.file.Path

class ConfigurationPlugin : Plugin<Project> {

  override fun apply(project: Project) {
    if (project != project.rootProject) {
      throw GradleException("Can only be applied to the root project")
    }

    val configurationLocations = project.objects.listProperty<Path>()
    configurationLocations.set(
      listOf(
        project.gradle.gradleUserHomeDir.toPath().resolve("dotfiles.conf"),
        project.projectDir.toPath().resolve("dotfiles.conf")
      )
    )

    project.extensions.create<ConfigLoaderExtension>(
      "dotfilesConfig",
      configurationLocations
    )
  }
}
