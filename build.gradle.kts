import com.github.benmanes.gradle.versions.updates.DependencyUpdates
import com.github.benmanes.gradle.versions.updates.DependencyUpdatesTask
import dotfilesbuild.io.file.EditFile
import org.gradle.api.tasks.Exec
import org.gradle.api.tasks.wrapper.Wrapper
import dotfilesbuild.io.file.Symlink
import dotfilesbuild.io.file.Mkdir
import dotfilesbuild.io.file.content.AppendIfNoLinesMatch
import dotfilesbuild.io.file.content.SetContent
import dotfilesbuild.io.git.CloneRepository
import dotfilesbuild.io.git.GitVersionControlTarget
import dotfilesbuild.io.git.PullRepository

plugins {
  id("com.github.ben-manes.versions") version "0.17.0"
  kotlin("jvm") version "1.2.41" apply false

  id("dotfilesbuild.intellij")
  id("dotfilesbuild.locations")
  id("dotfilesbuild.keepass")
  id("dotfilesbuild.self-update")
  id("dotfilesbuild.vcs-management")
  id("dotfilesbuild.git-vcs")
}

description = "Dotfiles and package management"

val personalWorkspaceDirectory: Directory = locations.workspace.dir("personal")
val workWorkspaceDirectory: Directory = locations.workspace.dir("work")
val codeLabWorkspaceDirectory: Directory = locations.workspace.dir("code_lab")

val dependencyUpdates by tasks.getting(DependencyUpdatesTask::class) {
  val rejectPatterns = listOf("alpha", "beta", "rc", "cr", "m").map { qualifier ->
    Regex("(?i).*[.-]$qualifier[.\\d-]*")
  }
  resolutionStrategy = closureOf<ResolutionStrategy> {
    componentSelection {
      all {
        if (rejectPatterns.any { it.matches(this.candidate.version) }) {
          this.reject("Release candidate")
        }
      }
    }
  }
}

// IntelliJ Regex:
// ^(\w+[:@/]+\w+.com[:/]?([\w\d-]+)/([\w\d-\.]+)\.git)$
// "$3"(GitVersionControlTarget::class) { origin("$1") }
versionControlTracking.invoke {
  "personal" {
    directory.set(locations.workspace.dir("personal"))
    groups.invoke {
      "apache" {
        vcs.invoke {
          "flink"(GitVersionControlTarget::class) { origin("https://github.com/apache/flink.git") }
        }
      }
      "arrow-kt" {
        vcs.invoke {
          "arrow"(GitVersionControlTarget::class) { origin("https://github.com/arrow-kt/arrow.git") }
        }
      }
      "arturbosch" {
        vcs.invoke {
          "detekt"(GitVersionControlTarget::class) { origin("https://github.com/arturbosch/detekt.git") }
        }
      }
      "bazelbuild" {
        vcs.invoke {
          "bazel"(GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/bazel.git") }
          "bazel-blog"(GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/bazel-blog.git") }
          "bazel-skylib"(GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/bazel-skylib.git") }
          "intellij"(GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/intellij.git") }
          "rules_go"(GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/rules_go.git") }
          "rules_kotlin"(GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/rules_kotlin.git") }
          "rules_webtesting"(GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/rules_webtesting.git") }
        }
      }
      "buildkite" {
        vcs.invoke {
          "agent"(GitVersionControlTarget::class) { origin("https://github.com/buildkite/agent.git") }
        }
      }
      "cloudbees" {
        vcs.invoke {
          "groovy-cps"(GitVersionControlTarget::class) { origin("https://github.com/cloudbees/groovy-cps.git") }
          "jenkins-scripts"(GitVersionControlTarget::class) { origin("https://github.com/cloudbees/jenkins-scripts.git") }
        }
      }
      "ethereum" {
        vcs.invoke {
          "ethereumj"(GitVersionControlTarget::class) { origin("https://github.com/ethereum/ethereumj.git") }
          "go-ethereum"(GitVersionControlTarget::class) { origin("https://github.com/ethereum/go-ethereum.git") }
          "pyethereum"(GitVersionControlTarget::class) { origin("https://github.com/ethereum/pyethereum.git") }
          "solidity"(GitVersionControlTarget::class) { origin("https://github.com/ethereum/solidity.git") }
          "wiki"(GitVersionControlTarget::class) { origin("https://github.com/ethereum/wiki.git") }
          "wiki.wiki"(GitVersionControlTarget::class) { origin("https://github.com/ethereum/wiki.wiki.git") }
        }
      }
      "github" {
        vcs.invoke {
          "training-kit"(GitVersionControlTarget::class) { origin("https://github.com/github/training-kit.git") }
        }
      }
      "google" {
        vcs.invoke {
          "copybara"(GitVersionControlTarget::class) { origin("https://github.com/google/copybara.git") }
          "protobuf-gradle-plugin"(GitVersionControlTarget::class) { origin("https://github.com/google/protobuf-gradle-plugin.git") }
        }
      }
      "gradle" {
        vcs.invoke {
          "gradle"(GitVersionControlTarget::class) { origin("https://github.com/gradle/gradle.git") }
          "gradle-completion"(GitVersionControlTarget::class) { origin("https://github.com/gradle/gradle-completion.git") }
          "gradle-profiler"(GitVersionControlTarget::class) { origin("https://github.com/gradle/gradle-profiler.git") }
          "kotlin-dsl"(GitVersionControlTarget::class) { origin("https://github.com/gradle/kotlin-dsl.git") }
        }
      }
      "grpc" {
        vcs.invoke {
          "grpc"(GitVersionControlTarget::class) { origin("https://github.com/grpc/grpc.git") }
          "grpc-java"(GitVersionControlTarget::class) { origin("https://github.com/grpc/grpc-java.git") }
          "grpc-go"(GitVersionControlTarget::class) { origin("https://github.com/grpc/grpc-go.git") }
        }
      }
      "jacoco" {
        vcs.invoke {
          "jacoco"(GitVersionControlTarget::class) { origin("https://github.com/jacoco/jacoco.git") }
        }
      }
      "jenkins" {
        vcs.invoke {
          "amazon-ecs-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/amazon-ecs-plugin.git") }
          "analysis-core-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/analysis-core-plugin.git") }
          "authorize-project-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/authorize-project-plugin.git") }
          "bitbucket-branch-source-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/bitbucket-branch-source-plugin.git") }
          "bitbucket-pullrequest-builder-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/bitbucket-pullrequest-builder-plugin.git") }
          "blueocean-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/blueocean-plugin.git") }
          "branch-api-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/branch-api-plugin.git") }
          "cloudbees-folder-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/cloudbees-folder-plugin.git") }
          "credentials-binding-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/credentials-binding-plugin.git") }
          "credentials-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/credentials-plugin.git") }
          "docker-build-publish-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-build-publish-plugin.git") }
          "docker-build-step-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-build-step-plugin.git") }
          "docker-commons-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-commons-plugin.git") }
          "docker-custom-build-environment-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-custom-build-environment-plugin.git") }
          "docker"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker.git") }
          "docker-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-plugin.git") }
          "docker-ssh-slave"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-ssh-slave.git") }
          "docker-traceability-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-traceability-plugin.git") }
          "docker-workflow-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-workflow-plugin.git") }
          "durable-task-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/durable-task-plugin.git") }
          "extended-choice-parameter-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/extended-choice-parameter-plugin.git") }
          "external-workspace-manager-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/external-workspace-manager-plugin.git") }
          "extras-executable-war"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/extras-executable-war.git") }
          "git-client-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/git-client-plugin.git") }
          "gitea-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/gitea-plugin.git") }
          "github-branch-source-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/github-branch-source-plugin.git") }
          "gitlab-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/gitlab-plugin.git") }
          "git-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/git-plugin.git") }
          "gradle-jpi-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/gradle-jpi-plugin.git") }
          "gradle-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/gradle-plugin.git") }
          "groovy-events-listener-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/groovy-events-listener-plugin.git") }
          "jenkins-design-language"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/jenkins-design-language.git") }
          "jenkins"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/jenkins.git") }
          "jenkins-test-harness"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/jenkins-test-harness.git") }
          "job-dsl-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/job-dsl-plugin.git") }
          "job-dsl-plugin.wiki"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/job-dsl-plugin.wiki.git") }
          "junit-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/junit-plugin.git") }
          "kubernetes-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/kubernetes-plugin.git") }
          "ldap-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/ldap-plugin.git") }
          "lockable-resources-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/lockable-resources-plugin.git") }
          "matrix-auth-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/matrix-auth-plugin.git") }
          "maven-hpi-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/maven-hpi-plugin.git") }
          "mercurial-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/mercurial-plugin.git") }
          "mesos-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/mesos-plugin.git") }
          "metrics-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/metrics-plugin.git") }
          "monitoring-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/monitoring-plugin.git") }
          "pipeline-build-step-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-build-step-plugin.git") }
          "pipeline-examples"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-examples.git") }
          "pipeline-input-step-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-input-step-plugin.git") }
          "pipeline-milestone-step-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-milestone-step-plugin.git") }
          "pipeline-model-definition-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-model-definition-plugin.git") }
          "pipeline-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-plugin.git") }
          "pipeline-stage-step-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-stage-step-plugin.git") }
          "pipeline-stage-view-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-stage-view-plugin.git") }
          "pipeline-utility-steps-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-utility-steps-plugin.git") }
          "plugin-pom"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/plugin-pom.git") }
          "scm-api-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/scm-api-plugin.git") }
          "script-security-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/script-security-plugin.git") }
          "ssh-slaves-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/ssh-slaves-plugin.git") }
          "swarm-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/swarm-plugin.git") }
          "throttle-concurrent-builds-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/throttle-concurrent-builds-plugin.git") }
          "workflow-aggregator-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-aggregator-plugin.git") }
          "workflow-api-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-api-plugin.git") }
          "workflow-basic-steps-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-basic-steps-plugin.git") }
          "workflow-cps-global-lib-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-cps-global-lib-plugin.git") }
          "workflow-cps-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-cps-plugin.git") }
          "workflow-durable-task-step-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-durable-task-step-plugin.git") }
          "workflow-job-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-job-plugin.git") }
          "workflow-multibranch-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-multibranch-plugin.git") }
          "workflow-remote-loader-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-remote-loader-plugin.git") }
          "workflow-scm-step-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-scm-step-plugin.git") }
          "workflow-step-api-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-step-api-plugin.git") }
          "workflow-support-plugin"(GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-support-plugin.git") }
        }
      }
      "JetBrains" {
        vcs.invoke {
          "intellij-community"(GitVersionControlTarget::class) { origin("https://github.com/JetBrains/intellij-community.git") }
          "kotlin"(GitVersionControlTarget::class) { origin("https://github.com/JetBrains/kotlin.git") }
          "teamcity-achievements"(GitVersionControlTarget::class) { origin("https://github.com/JetBrains/teamcity-achievements.git") }
          "teamcity-commit-hooks"(GitVersionControlTarget::class) { origin("https://github.com/JetBrains/teamcity-commit-hooks.git") }
          "TeamCity.GitHubIssues"(GitVersionControlTarget::class) { origin("https://github.com/JetBrains/TeamCity.GitHubIssues.git") }
          "teamcity-google-agent"(GitVersionControlTarget::class) { origin("https://github.com/JetBrains/teamcity-google-agent.git") }
          "teamcity-local-cloud"(GitVersionControlTarget::class) { origin("https://github.com/JetBrains/teamcity-local-cloud.git") }
          "TeamCity.QueueManager"(GitVersionControlTarget::class) { origin("https://github.com/JetBrains/TeamCity.QueueManager.git") }
          "teamcity-sdk-maven-plugin"(GitVersionControlTarget::class) { origin("https://github.com/JetBrains/teamcity-sdk-maven-plugin.git") }
        }
      }
      "joel-costigliola" {
        vcs.invoke {

        }
      }
      "junit-team" {
        vcs.invoke {
          "junit5"(GitVersionControlTarget::class) { origin("https://github.com/junit-team/junit5.git") }
          "junit5-samples"(GitVersionControlTarget::class) { origin("https://github.com/junit-team/junit5-samples.git") }
        }
      }
      "Kotlin" {
        vcs.invoke {
          "dokka"(GitVersionControlTarget::class) { origin("https://github.com/Kotlin/dokka.git") }
          "KEEP"(GitVersionControlTarget::class) { origin("https://github.com/Kotlin/KEEP.git") }
          "kotlinx.coroutines"(GitVersionControlTarget::class) { origin("https://github.com/Kotlin/kotlinx.coroutines.git") }
        }
      }
      "kubernetes" {
        vcs.invoke {
          "autoscaler"(GitVersionControlTarget::class) { origin("https://github.com/kubernetes/autoscaler.git") }
          "charts"(GitVersionControlTarget::class) { origin("https://github.com/kubernetes/charts.git") }
          "helm"(GitVersionControlTarget::class) { origin("https://github.com/kubernetes/helm.git") }
          "kubernetes"(GitVersionControlTarget::class) { origin("https://github.com/kubernetes/kubernetes.git") }
        }
      }
      "mkobit" {
        vcs.invoke {
          "blog"(GitVersionControlTarget::class) { origin("git@gitlab.com:mkobit/blog.git") }
          "gradle-assertions"(GitVersionControlTarget::class) { origin("git@github.com:mkobit/gradle-assertions.git") }
          "gradle-junit-jupiter-extensions"(GitVersionControlTarget::class) { origin("git@github.com:mkobit/gradle-junit-jupiter-extensions.git") }
          "gradle-junit-platform-tools"(GitVersionControlTarget::class) { origin("git@github.com:mkobit/gradle-junit-platform-tools.git") }
          "jenkins-pipeline-shared-libraries-gradle-plugin"(GitVersionControlTarget::class) { origin("git@github.com:mkobit/jenkins-pipeline-shared-libraries-gradle-plugin.git") }
          "jenkins-pipeline-shared-library-example"(GitVersionControlTarget::class) { origin("git@github.com:mkobit/jenkins-pipeline-shared-library-example.git") }
          "jenkins-scripts"(GitVersionControlTarget::class) { origin("git@github.com:mkobit/jenkins-scripts.git") }
          "junit5-dynamodb-local-extension"(GitVersionControlTarget::class) { origin("git@github.com:mkobit/junit5-dynamodb-local-extension.git") }
        }
      }
      "mesonbuild" {
        vcs.invoke {
          "meson"(GitVersionControlTarget::class) { origin("https://github.com/mesonbuild/meson.git") }
        }
      }
      "ratpack" {
        vcs.invoke {
          "ratpack"(GitVersionControlTarget::class) { origin("https://github.com/ratpack/ratpack.git") }
        }
      }
      "salesforce" {
        vcs.invoke {
          "grpc-java-contrib"(GitVersionControlTarget::class) { origin("https://github.com/salesforce/grpc-java-contrib.git") }
        }
      }
      "square" {
        vcs.invoke {
          "javapoet"(GitVersionControlTarget::class) { origin("https://github.com/square/javapoet.git") }
          "kotlinpoet"(GitVersionControlTarget::class) { origin("https://github.com/square/kotlinpoet.git") }
          "okhttp"(GitVersionControlTarget::class) { origin("https://github.com/square/okhttp.git") }
          "retrofit"(GitVersionControlTarget::class) { origin("https://github.com/square/retrofit.git") }
        }
      }
      "willowtreeapps" {
        vcs.invoke {
          "assertk"(GitVersionControlTarget::class) { origin("https://github.com/willowtreeapps/assertk.git") }
        }
      }
    }
  }
}

tasks {
  val personalWorkspace by creating(Mkdir::class) {
    directory.set(personalWorkspaceDirectory)
  }

  val workWorkspace by creating(Mkdir::class) {
    directory.set(workWorkspaceDirectory)
  }

  val codeLabWorkspace by creating(Mkdir::class) {
    directory.set(codeLabWorkspaceDirectory)
  }

  val workspace by creating {
    group = "Workspace"
    dependsOn(personalWorkspace, workWorkspace, codeLabWorkspace)
  }

  val gitConfigGeneration by creating(EditFile::class) {
    val gitConfigGeneral = projectFile("git/gitconfig_general.dotfile")
    val gitConfigPersonal = projectFile("git/gitconfig_personal.dotfile")
    editActions.set(listOf(
        SetContent {
          """
              [include]
                  path = ${gitConfigGeneral.asFile.absolutePath}
              [includeIf "gitdir:${project.rootDir.absolutePath}/"]
                  path = ${gitConfigPersonal.asFile.absolutePath}
              [includeIf "gitdir:${personalWorkspace.directory.asFile.get().absolutePath}/"]
                  path = ${gitConfigPersonal.asFile.absolutePath}
              [includeIf "gitdir:${codeLabWorkspace.directory.asFile.get().absolutePath}/"]
                  path = ${gitConfigPersonal.asFile.absolutePath}
              [includeIf "gitdir:${workWorkspace.directory.asFile.get().absolutePath}/"]
                  path = ${locations.home.file(".gitconfig_work")}
          """.trimIndent()
        }
    ))
    file.set(locations.home.file(".gitconfig"))
    dependsOn(workspace)
  }

  val gitIgnoreGlobal by creating(Symlink::class) {
    source.set(projectFile("git/gitignore_global.dotfile"))
    destination.set(locations.home.file(".gitignore_global"))
  }

  val git by creating {
    group = "Git"
    dependsOn(gitConfigGeneration, gitIgnoreGlobal)
  }

  val screenRc by creating(Symlink::class) {
    source.set(projectFile("screen/screenrc.dotfile"))
    destination.set(locations.home.file(".screenrc"))
  }

  val screen by creating {
    group = "Screen"
    dependsOn(screenRc)
  }

  val tmuxConf by creating(Symlink::class) {
    source.set(projectFile("tmux/tmux.conf.dotfile"))
    destination.set(locations.home.file(".tmux.conf"))
  }

  val sshCms by creating(Mkdir::class) {
    directory.set(locations.home.dir(".ssh/controlMaster"))
  }

  val ssh by creating {
    group = "SSH"
    dependsOn(sshCms)
  }

  val tmux by creating {
    group = "Tmux"
    dependsOn(tmuxConf)
  }

  val vimRc by creating(Symlink::class) {
    source.set(projectFile("vim/vimrc.dotfile"))
    destination.set(locations.home.file(".vimrc"))
  }

  val vim by creating {
    group = "VIM"
    dependsOn(vimRc)
  }

  val zshrcDotfiles by creating(EditFile::class) {
    description = "Creates a ZSH file to be sourced that only contains dotfiles specific content"
    file.set(locations.home.file(".zshrc_dotfiles"))
    // TODO: add Provider<Directory> to VersionControlTarget
    val gradleCompletion = versionControlTracking["personal"].groups["gradle"].vcs["gradle-completion"]
    editActions.add(provider {
      val functions = layout.projectDirectory.file("zsh/functions.source")
      val text = ". ${functions.asFile.absolutePath} # dotfiles: functions.source"
      AppendIfNoLinesMatch(
          Regex(text, RegexOption.LITERAL),
          { text }
      )
    })
    editActions.add(provider {
      val aliases = layout.projectDirectory.file("zsh/aliases.source")
      val text = ". ${aliases.asFile.absolutePath} # dotfiles: aliases.source"
      AppendIfNoLinesMatch(
          Regex(text, RegexOption.LITERAL),
          { text }
      )
    })
  }

  val zshrcFile by creating(EditFile::class) {
    description = "Edits the .zshrc file"
    file.set(locations.home.file(".zshrc"))
    dependsOn(zshrcDotfiles)
    editActions.add(provider {
      val text = ". ${zshrcDotfiles.file.get().asFile.toPath().toAbsolutePath()}"
      AppendIfNoLinesMatch(
          Regex(text, RegexOption.LITERAL),
          { text }
      )
    })
  }

  val zsh by creating {
    group = "ZSH"
    description = "Sets up ZSH"
    dependsOn(zshrcDotfiles, zshrcFile)
  }

  "wrapper"(Wrapper::class) {
    gradleVersion = "4.8"
  }

  "dotfiles" {
    description = "Sets up all dotfiles and packages"
    group = "Install"
    dependsOn(git, screen, ssh, tmux, vim, workspace, zsh)
  }
}

intellij {
  intellijVersion.set("2018.1")
}

keepass {
  keepassVersion.set("2.39")
}
