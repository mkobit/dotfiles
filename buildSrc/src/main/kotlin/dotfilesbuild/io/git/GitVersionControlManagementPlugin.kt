package dotfilesbuild.io.git

import dotfilesbuild.io.vcs.VersionControlManagementPlugin
import dotfilesbuild.io.vcs.VersionControlOrganization
import org.gradle.api.NamedDomainObjectContainer
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.provider.ProviderFactory
import org.gradle.api.reflect.TypeOf
// TODO: remove star imports after getValue issue it resolved
import org.gradle.kotlin.dsl.*
import javax.inject.Inject

open class GitVersionControlManagementPlugin @Inject constructor(
    private val providerFactory: ProviderFactory
) : Plugin<Project> {
  override fun apply(target: Project) {
    target.run {
      val refreshAllGitRepositories= tasks.register("refreshAllGitRepositories") {
        group = "Git Management"
        description = "Refreshes all Git repositories"
      }
      pluginManager.apply(VersionControlManagementPlugin::class.java)
      val containerType = object : TypeOf<NamedDomainObjectContainer<VersionControlOrganization>>() {}
      extensions.configure(containerType) {
        whenObjectAdded {
          val organizationClassifier = "Organization${name.capitalize()}"
          val refreshOrganization = tasks.register("refresh${organizationClassifier}GitRepositories") {
            description = "Refreshes Git repositories for organization ${name.capitalize()}"
          }
          refreshAllGitRepositories.configure {
            dependsOn(refreshOrganization)
          }
          groups.whenObjectAdded {
            val versionControlGroup = this
            vcs.registerFactory(GitVersionControlTarget::class.java) { name ->
              // TODO: make the directory a part of this target
              GitVersionControlTarget(name, emptyMap(), versionControlGroup.directory.map { it.dir(name) })
            }
            val groupClassifier = "Group${name.capitalize()}"
            val refreshGroup = tasks.register("refresh${organizationClassifier}${groupClassifier}GitRepositories") {
              description = "Refresh group ${versionControlGroup.name} Git repositories"
            }
            refreshOrganization.configure {
              dependsOn(refreshGroup)
            }
            vcs.withType<GitVersionControlTarget>().configureEach {
              val gitVersionControlTarget = this
              val targetClassifier = "GitRepository$name"
              // TODO: better handle multiple remotes
              val cloneRepository = tasks.register("clone$organizationClassifier$groupClassifier$targetClassifier",
                  CloneRepository::class.java) {
                description = "Clone Git repository ${gitVersionControlTarget.name}"
                repositoryDirectory.set(gitVersionControlTarget.directory)
                repositoryUrl.set(providerFactory.provider {
                  gitVersionControlTarget.remotes["origin"] ?: gitVersionControlTarget.remotes.entries.first().value
                })
              }
              val pullRepository = tasks.register("pull$organizationClassifier$groupClassifier$targetClassifier",
                  PullRepository::class.java) {
                description = "Pull Git repository ${gitVersionControlTarget.name}"
                dependsOn(cloneRepository)
                repositoryDirectory.set(cloneRepository.map(CloneRepository::repositoryDirectory).get())
              }
              refreshGroup.configure {
                dependsOn(pullRepository)
              }
            }
          }
        }
      }
    }
  }
}
