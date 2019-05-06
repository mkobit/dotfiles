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
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.container
import org.gradle.kotlin.dsl.getByType
import org.gradle.kotlin.dsl.newInstance
import org.gradle.kotlin.dsl.register
import javax.inject.Inject

class VersionControlManagementPlugin @Inject constructor(private val instantiator: Instantiator) : Plugin<Project> {

  companion object {
    private const val EXTENSION_NAME = "versionControlTracking"
  }

  override fun apply(target: Project) {
    target.run {
      apply<LocationsPlugin>()
      val locations = extensions.getByType(LocationsExtension::class)
      val topLevelContainer = container(VersionControlOrganization::class) { orgName ->
        val createOrganization = tasks.register("createVersionControlOrganization${orgName.capitalize()}", Mkdir::class) {
          description = "Create directory for organizational unit $orgName"
          directory.set(locations.workspace.dir(orgName))
        }
          // TODO: determine how we can prevent eager configuration of the tasks
        VersionControlOrganization(orgName, createOrganization.map(Mkdir::directory).get(), container(VersionControlGroup::class) { groupName ->
          val createGroup = tasks.register("createVersionControlGroup${groupName.capitalize()}", Mkdir::class) {
            description = "Create directory for grouping unit $groupName"
            directory.set(createOrganization.map { it.directory.dir(groupName) }.get())
          }
          // TODO: determine how we can prevent eager configuration of the tasks
          VersionControlGroup(
              groupName,
              createGroup.map(Mkdir::directory).map { it.get() },
              objects.newInstance(DefaultVersionControlManagementContainer::class, instantiator)
          )
        })
      }

      val extensionType = object : TypeOf<NamedDomainObjectContainer<VersionControlOrganization>>() {}
      extensions.add(extensionType, EXTENSION_NAME, topLevelContainer)
    }
  }
}
