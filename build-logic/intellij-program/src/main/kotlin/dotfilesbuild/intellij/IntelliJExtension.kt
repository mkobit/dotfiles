package dotfilesbuild.intellij

import org.gradle.api.provider.Property

open class IntelliJExtension(
  val intellijVersion: Property<String>,
  val distributionType: Property<Distribution>
)
