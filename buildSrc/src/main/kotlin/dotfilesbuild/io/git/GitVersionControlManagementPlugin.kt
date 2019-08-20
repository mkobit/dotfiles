package dotfilesbuild.io.git

// TODO: remove star imports after getValue issue it resolved
import dotfilesbuild.io.vcs.VersionControlManagementPlugin
import dotfilesbuild.io.vcs.VersionControlOrganization
import org.gradle.api.NamedDomainObjectContainer
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.provider.ProviderFactory
import org.gradle.api.reflect.TypeOf
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.register
import org.gradle.kotlin.dsl.withType
import javax.inject.Inject

class GitVersionControlManagementPlugin @Inject constructor(
  private val providerFactory: ProviderFactory
) : Plugin<Project> {
  override fun apply(target: Project) {
    target.run {
      apply<VersionControlManagementPlugin>()
      val refreshAllGitRepositories = tasks.register("refreshAllGitRepositories") {
        group = "Git Management"
        description = "Refreshes all Git repositories"
      }
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
            vcs.withType<GitVersionControlTarget>().all {
              val gitVersionControlTarget = this
              val targetClassifier = "GitRepository$name"
              val fullClassifier = "$organizationClassifier$groupClassifier$targetClassifier"
              // TODO: better handle multiple remotes
              val configureRepository = tasks.register("configure$fullClassifier", ManageGitRepository::class) {
                description = "Synchronizes and configures Git repository ${gitVersionControlTarget.name}"
                gitRepositorySpec.set(gitVersionControlTarget)
              }
              refreshGroup.configure {
                dependsOn(configureRepository)
              }
            }
          }
        }
      }
    }
  }
}
