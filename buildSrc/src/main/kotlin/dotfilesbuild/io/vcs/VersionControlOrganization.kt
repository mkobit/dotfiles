package dotfilesbuild.io.vcs

import org.gradle.api.Named
import org.gradle.api.NamedDomainObjectContainer
import org.gradle.api.file.DirectoryProperty

class VersionControlOrganization(
    private val organizationName: String,
    val directory: DirectoryProperty,
    val groups: NamedDomainObjectContainer<VersionControlGroup>
) : Named {
  override fun getName(): String = organizationName
}
