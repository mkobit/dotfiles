package dotfilesbuild.io.vcs

import dotfilesbuild.io.vcs.internal.DefaultVersionControlManagementContainer
import org.gradle.api.NamedDomainObjectContainer
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.reflect.TypeOf
import org.gradle.internal.reflect.Instantiator
import javax.inject.Inject

open class VersionControlManagementPlugin @Inject constructor(private val instantiator: Instantiator) : Plugin<Project> {

  companion object {
    private const val EXTENSION_NAME = "versionControlTracking"
  }


  override fun apply(target: Project) {
    target.run {
      val topLevelContainer = container(VersionControlOrganization::class.java) { orgName ->
        val orgDir = layout.directoryProperty()
        VersionControlOrganization(orgName, orgDir, container(VersionControlGroup::class.java) { groupName ->
          VersionControlGroup(
              groupName,
              orgDir.dir(groupName),
              objects.newInstance(DefaultVersionControlManagementContainer::class.java, instantiator)
          )
        })
      }

      val extensionType = object : TypeOf<NamedDomainObjectContainer<VersionControlOrganization>>() {}
      extensions.add(extensionType, EXTENSION_NAME, topLevelContainer)
    }
  }
}
