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
      apply<VersionControlManagementPlugin>()
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
            // TODO: make laziness actually work
            vcs.withType<GitVersionControlTarget>().whenObjectAdded {
              val gitVersionControlTarget = this
              val targetClassifier = "GitRepository$name"
              val fullClassifier = "$organizationClassifier$groupClassifier$targetClassifier"
              // TODO: better handle multiple remotes
              val cloneRepository = tasks.register("clone$fullClassifier",
                  CloneRepository::class) {
                description = "Clone Git repository ${gitVersionControlTarget.name}"
                repositoryDirectory.set(gitVersionControlTarget.directory)
                repositoryUrl.set(providerFactory.provider {
                  gitVersionControlTarget.remotes["origin"] ?: gitVersionControlTarget.remotes.entries.first().value
                })
              }
              val configureRemotes = tasks.register("configureRemotes$fullClassifier", ConfigureRemotes::class) {
                dependsOn(cloneRepository)
                description = "Configure remotes for Git repository ${gitVersionControlTarget.name}"
                repositoryDirectory.set(cloneRepository.map(CloneRepository::repositoryDirectory).get())
                remotes.set(providerFactory.provider { gitVersionControlTarget.remotes })
              }
              val fetchRemotes = tasks.register("fetchRemotes$fullClassifier", FetchRemotes::class) {
                dependsOn(configureRemotes)
                description = "Fetch remotes for Git repository ${gitVersionControlTarget.name}"
                repositoryDirectory.set(cloneRepository.map(CloneRepository::repositoryDirectory).get())
              }
              val pullRepository = tasks.register("pull$fullClassifier",
                  PullRepository::class) {
                dependsOn(fetchRemotes)
                description = "Pull Git repository ${gitVersionControlTarget.name}"
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
