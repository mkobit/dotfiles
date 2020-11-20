package dotfilesbuild.config

import com.typesafe.config.Config
import org.gradle.api.provider.Provider

open class ConfigLookupExtension(val config: Provider<Config>)
