package dotfilesbuild.config

import com.typesafe.config.ConfigFactory
import org.gradle.api.provider.ListProperty
import java.nio.file.Path

open class ConfigLoaderExtension(
  val sources: ListProperty<Path>
) {

  private val configuration =
    sources.map { configurationFiles ->
      configurationFiles
        .map { it.toFile() }
        .map { ConfigFactory.parseFile(it) }
        .reduce { first, second -> first.withFallback(second) }
    }.orElse(ConfigFactory.empty())
}
