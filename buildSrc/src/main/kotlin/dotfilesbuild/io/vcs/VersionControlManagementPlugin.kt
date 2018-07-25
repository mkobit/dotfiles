package dotfilesbuild.io.vcs

import dotfilesbuild.LocationsExtension
import dotfilesbuild.LocationsPlugin
import dotfilesbuild.io.file.Mkdir
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
      pluginManager.apply(LocationsPlugin::class.java)
      val locations = extensions.findByType(LocationsExtension::class.java)!!
      val topLevelContainer = container(VersionControlOrganization::class.java) { orgName ->
        val createOrganization = tasks.register("createVersionControlOrganization${orgName.capitalize()}", Mkdir::class.java) {
          description = "Create directory for organizational unit $orgName"
          directory.set(locations.workspace.dir(orgName))
        }
        val m = createOrganization.map(Mkdir::directory).map { it.get() }
          // TODO: determine how we can prevent eager configuration of the tasks
        VersionControlOrganization(orgName, createOrganization.map(Mkdir::directory).get(), container(VersionControlGroup::class.java) { groupName ->
          val createGroup = tasks.register("createVersionControlGroup${groupName.capitalize()}", Mkdir::class.java) {
            description = "Create directory for grouping unit $groupName"
            directory.set(createOrganization.map { it.directory.dir(groupName) }.get())
          }
          // TODO: determine how we can prevent eager configuration of the tasks
          VersionControlGroup(
              groupName,
              createGroup.map(Mkdir::directory).map { it.get() },
              objects.newInstance(DefaultVersionControlManagementContainer::class.java, instantiator)
          )
        })
      }

      val extensionType = object : TypeOf<NamedDomainObjectContainer<VersionControlOrganization>>() {}
      extensions.add(extensionType, EXTENSION_NAME, topLevelContainer)
    }
  }
}
