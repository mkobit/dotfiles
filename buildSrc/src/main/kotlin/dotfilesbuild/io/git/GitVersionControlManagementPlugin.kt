package dotfilesbuild.io.git

import dotfilesbuild.io.vcs.VersionControlManagementPlugin
import dotfilesbuild.io.vcs.VersionControlOrganization
import org.gradle.api.NamedDomainObjectContainer
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.reflect.TypeOf
import org.gradle.kotlin.dsl.withType

open class GitVersionControlManagementPlugin : Plugin<Project> {
  override fun apply(target: Project) {
    target.run {
      pluginManager.apply(VersionControlManagementPlugin::class.java)
      val containerType = object : TypeOf<NamedDomainObjectContainer<VersionControlOrganization>>() {}
      extensions.configure(containerType) {
        whenObjectAdded {
          groups.whenObjectAdded {
            vcs.registerFactory(GitVersionControlTarget::class.java) { name ->
              GitVersionControlTarget(name, emptyMap())
            }
            vcs.withType<GitVersionControlTarget> {
              // TODO: create pull. clone, and other tasks
            }
          }
        }
      }
    }
  }
}
