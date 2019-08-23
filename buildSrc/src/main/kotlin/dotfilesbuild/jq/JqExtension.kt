package dotfilesbuild.jq

import org.gradle.api.provider.Property

open class JqExtension(
  val jqVersion: Property<String>,
  val checksum: Property<String>
)
