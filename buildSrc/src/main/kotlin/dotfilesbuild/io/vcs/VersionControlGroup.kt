package dotfilesbuild.io.vcs

import org.gradle.api.ExtensiblePolymorphicDomainObjectContainer
import org.gradle.api.Named
import org.gradle.api.file.Directory
import org.gradle.api.provider.Provider

class VersionControlGroup(
  private val groupName: String,
  val directory: Provider<Directory>,
  val vcs: ExtensiblePolymorphicDomainObjectContainer<VersionControlTarget>
) : ExtensiblePolymorphicDomainObjectContainer<VersionControlTarget> by vcs, Named {

  init {
    require(groupName.trim() == groupName) { "groupName '$name' must not begin or end with whitespace" }
  }

  override fun getName(): String = groupName
}
