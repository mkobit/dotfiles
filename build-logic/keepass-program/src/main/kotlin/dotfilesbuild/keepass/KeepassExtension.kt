package dotfilesbuild.keepass

import org.gradle.api.file.RegularFileProperty
import org.gradle.api.provider.Property

open class KeepassExtension(
  val keepassVersion: Property<String>,
  val secretFile: RegularFileProperty
)
