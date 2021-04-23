package dotfilesbuild.config

import com.typesafe.config.Config
import com.typesafe.config.ConfigException
import com.typesafe.config.ConfigFactory
import org.gradle.api.Project
import org.gradle.api.provider.ListProperty
import org.gradle.api.provider.Provider
import java.nio.file.Path

open class ConfigLoaderExtension(
  @SuppressWarnings("MemberVisibilityCanBePrivate") val sources: ListProperty<Path>
) {

  internal fun configFor(project: Project): Provider<Config> = if (project == project.rootProject) {
    configuration
  } else {
    val configPath = project.path.substring(1).replace(":", ".")
    configuration.map {
      try {
        it.getConfig(configPath)
      } catch (missing: ConfigException.Missing) {
        ConfigFactory.empty()
      }
    }
  }

  private val configuration =
    sources.map { configurationFiles ->
      configurationFiles
        .map { it.toFile() }
        .map { ConfigFactory.parseFile(it) }
        .reduce { first, second -> first.withFallback(second) }
    }.orElse(ConfigFactory.empty())
}
