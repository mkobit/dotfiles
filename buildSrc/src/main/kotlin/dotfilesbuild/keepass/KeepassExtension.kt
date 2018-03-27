package dotfilesbuild.keepass

import org.gradle.api.file.DirectoryProperty
import org.gradle.api.provider.Property

open class KeepassExtension(
    val keepassVersion: Property<String>,
    val downloadDirectory: DirectoryProperty,
    val installDirectory: DirectoryProperty
)
