import dotfilesbuild.projectFile
import dotfilesbuild.io.file.EditFile
import dotfilesbuild.io.file.Mkdir
import dotfilesbuild.io.file.Symlink
import dotfilesbuild.io.file.content.SetContent
import dotfilesbuild.io.git.GitVersionControlTarget

plugins {
  id("com.gradle.build-scan") version "2.3"
  id("com.github.ben-manes.versions") version "0.22.0"
  id("org.jlleitschuh.gradle.ktlint") version "8.2.0"
  id("org.jetbrains.gradle.plugin.idea-ext") version "0.5" apply false

  dotfilesbuild.`dotfiles-lifecycle`

  dotfilesbuild.locations
  dotfilesbuild.`self-update`
  dotfilesbuild.`vcs-management`
  dotfilesbuild.`git-vcs`

  dotfilesbuild.shell.`generated-zsh`
  dotfilesbuild.shell.`managed-bin`
  dotfilesbuild.shell.`source-bin`
  dotfilesbuild.shell.`unmanaged-bin`
  dotfilesbuild.shell.`zsh-aliases-and-functions`
}

buildScan {
  termsOfServiceUrl = "https://gradle.com/terms-of-service"
  termsOfServiceAgree = "yes"
}

description = "Dotfiles and package management"

val personalWorkspaceDirectory: Directory = locations.workspace.dir("personal")
val workWorkspaceDirectory: Directory = locations.workspace.dir("work")
val codeLabWorkspaceDirectory: Directory = locations.workspace.dir("code_lab")

ktlint {
  version.set("0.32.0")
}

repositories {
  jcenter()
}

// IntelliJ Regex:
// ^(\w+[:@/]+\w+.com[:/]?([\w\d-]+)/([\w\d-\.]+)\.git)$
// "$3"(GitVersionControlTarget::class) { origin("$1") }
versionControlTracking {
  register("personal") {
    directory.set(locations.workspace.dir("personal"))
    groups {
      register("apache") {
        vcs {
          register("flink", GitVersionControlTarget::class) { origin("https://github.com/apache/flink.git") }
        }
      }
      register("arrow-kt") {
        vcs {
          register("arrow", GitVersionControlTarget::class) { origin("https://github.com/arrow-kt/arrow.git") }
        }
      }
      register("arturbosch") {
        vcs {
          register("detekt", GitVersionControlTarget::class) { origin("https://github.com/arturbosch/detekt.git") }
        }
      }
      register("bazelbuild") {
        vcs {
          register("bazel", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/bazel.git") }
          register("bazel-blog", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/bazel-blog.git") }
          register("bazel-skylib", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/bazel-skylib.git") }
          register("intellij", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/intellij.git") }
          register("rules_go", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/rules_go.git") }
          register("rules_kotlin", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/rules_kotlin.git") }
          register("rules_webtesting", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/rules_webtesting.git") }
        }
      }
      register("buildkite") {
        vcs {
          register("agent", GitVersionControlTarget::class) { origin("https://github.com/buildkite/agent.git") }
        }
      }
      register("cloudbees") {
        vcs {
          register("groovy-cps", GitVersionControlTarget::class) { origin("https://github.com/cloudbees/groovy-cps.git") }
          register("jenkins-scripts", GitVersionControlTarget::class) { origin("https://github.com/cloudbees/jenkins-scripts.git") }
        }
      }
      register("ethereum") {
        vcs {
          register("ethereumj", GitVersionControlTarget::class) { origin("https://github.com/ethereum/ethereumj.git") }
          register("go-ethereum", GitVersionControlTarget::class) { origin("https://github.com/ethereum/go-ethereum.git") }
          register("pyethereum", GitVersionControlTarget::class) { origin("https://github.com/ethereum/pyethereum.git") }
          register("solidity", GitVersionControlTarget::class) { origin("https://github.com/ethereum/solidity.git") }
          register("wiki", GitVersionControlTarget::class) { origin("https://github.com/ethereum/wiki.git") }
          register("wiki.wiki", GitVersionControlTarget::class) { origin("https://github.com/ethereum/wiki.wiki.git") }
        }
      }
      register("github") {
        vcs {
          register("training-kit", GitVersionControlTarget::class) { origin("https://github.com/github/training-kit.git") }
        }
      }
      register("google") {
        vcs {
          register("copybara", GitVersionControlTarget::class) { origin("https://github.com/google/copybara.git") }
          register("protobuf-gradle-plugin", GitVersionControlTarget::class) {
            origin("https://github.com/google/protobuf-gradle-plugin.git")
            remote("personal", "git@github.com:mkobit/protobuf-gradle-plugin.git")
          }
        }
      }
      register("gradle") {
        vcs {
          register("gradle", GitVersionControlTarget::class) {
            origin("https://github.com/gradle/gradle.git")
            remote("personal", "git@github.com:mkobit/gradle.git")
          }
          register("gradle-completion", GitVersionControlTarget::class) { origin("https://github.com/gradle/gradle-completion.git") }
          register("gradle-profiler", GitVersionControlTarget::class) { origin("https://github.com/gradle/gradle-profiler.git") }
          register("kotlin-dsl", GitVersionControlTarget::class) {
            origin("https://github.com/gradle/kotlin-dsl.git")
            remote("personal", "git@github.com:mkobit/kotlin-dsl.git")
          }
        }
      }
      register("grpc") {
        vcs {
          register("grpc", GitVersionControlTarget::class) { origin("https://github.com/grpc/grpc.git") }
          register("grpc-java", GitVersionControlTarget::class) { origin("https://github.com/grpc/grpc-java.git") }
          register("grpc-go", GitVersionControlTarget::class) { origin("https://github.com/grpc/grpc-go.git") }
        }
      }
      register("jacoco") {
        vcs {
          register("jacoco", GitVersionControlTarget::class) { origin("https://github.com/jacoco/jacoco.git") }
        }
      }
      register("jenkins") {
        vcs {
          register("amazon-ecs-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/amazon-ecs-plugin.git") }
          register("analysis-core-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/analysis-core-plugin.git") }
          register("authorize-project-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/authorize-project-plugin.git") }
          register("bitbucket-branch-source-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/bitbucket-branch-source-plugin.git") }
          register("bitbucket-pullrequest-builder-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/bitbucket-pullrequest-builder-plugin.git") }
          register("blueocean-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/blueocean-plugin.git") }
          register("branch-api-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/branch-api-plugin.git") }
          register("cloudbees-folder-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/cloudbees-folder-plugin.git") }
          register("credentials-binding-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/credentials-binding-plugin.git") }
          register("credentials-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/credentials-plugin.git") }
          register("docker-build-publish-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-build-publish-plugin.git") }
          register("docker-build-step-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-build-step-plugin.git") }
          register("docker-commons-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-commons-plugin.git") }
          register("docker-custom-build-environment-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-custom-build-environment-plugin.git") }
          register("docker", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker.git") }
          register("docker-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-plugin.git") }
          register("docker-ssh-slave", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-ssh-slave.git") }
          register("docker-traceability-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-traceability-plugin.git") }
          register("docker-workflow-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/docker-workflow-plugin.git") }
          register("durable-task-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/durable-task-plugin.git") }
          register("extended-choice-parameter-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/extended-choice-parameter-plugin.git") }
          register("external-workspace-manager-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/external-workspace-manager-plugin.git") }
          register("extras-executable-war", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/extras-executable-war.git") }
          register("git-client-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/git-client-plugin.git") }
          register("gitea-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/gitea-plugin.git") }
          register("github-branch-source-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/github-branch-source-plugin.git") }
          register("gitlab-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/gitlab-plugin.git") }
          register("git-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/git-plugin.git") }
          register("gradle-jpi-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/gradle-jpi-plugin.git") }
          register("gradle-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/gradle-plugin.git") }
          register("groovy-events-listener-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/groovy-events-listener-plugin.git") }
          register("jenkins-design-language", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/jenkins-design-language.git") }
          register("jenkins", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/jenkins.git") }
          register("jenkins-test-harness", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/jenkins-test-harness.git") }
          register("job-dsl-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/job-dsl-plugin.git") }
          register("job-dsl-plugin.wiki", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/job-dsl-plugin.wiki.git") }
          register("junit-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/junit-plugin.git") }
          register("kubernetes-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/kubernetes-plugin.git") }
          register("ldap-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/ldap-plugin.git") }
          register("lockable-resources-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/lockable-resources-plugin.git") }
          register("matrix-auth-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/matrix-auth-plugin.git") }
          register("maven-hpi-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/maven-hpi-plugin.git") }
          register("mercurial-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/mercurial-plugin.git") }
          register("mesos-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/mesos-plugin.git") }
          register("metrics-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/metrics-plugin.git") }
          register("monitoring-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/monitoring-plugin.git") }
          register("pipeline-build-step-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-build-step-plugin.git") }
          register("pipeline-examples", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-examples.git") }
          register("pipeline-input-step-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-input-step-plugin.git") }
          register("pipeline-milestone-step-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-milestone-step-plugin.git") }
          register("pipeline-model-definition-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-model-definition-plugin.git") }
          register("pipeline-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-plugin.git") }
          register("pipeline-stage-step-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-stage-step-plugin.git") }
          register("pipeline-stage-view-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-stage-view-plugin.git") }
          register("pipeline-utility-steps-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/pipeline-utility-steps-plugin.git") }
          register("plugin-pom", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/plugin-pom.git") }
          register("scm-api-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/scm-api-plugin.git") }
          register("script-security-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/script-security-plugin.git") }
          register("ssh-slaves-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/ssh-slaves-plugin.git") }
          register("swarm-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/swarm-plugin.git") }
          register("throttle-concurrent-builds-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/throttle-concurrent-builds-plugin.git") }
          register("workflow-aggregator-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-aggregator-plugin.git") }
          register("workflow-api-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-api-plugin.git") }
          register("workflow-basic-steps-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-basic-steps-plugin.git") }
          register("workflow-cps-global-lib-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-cps-global-lib-plugin.git") }
          register("workflow-cps-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-cps-plugin.git") }
          register("workflow-durable-task-step-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-durable-task-step-plugin.git") }
          register("workflow-job-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-job-plugin.git") }
          register("workflow-multibranch-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-multibranch-plugin.git") }
          register("workflow-remote-loader-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-remote-loader-plugin.git") }
          register("workflow-scm-step-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-scm-step-plugin.git") }
          register("workflow-step-api-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-step-api-plugin.git") }
          register("workflow-support-plugin", GitVersionControlTarget::class) { origin("https://github.com/jenkinsci/workflow-support-plugin.git") }
        }
      }
      register("JetBrains") {
        vcs {
          register("intellij-community", GitVersionControlTarget::class) { origin("https://github.com/JetBrains/intellij-community.git") }
          register("kotlin", GitVersionControlTarget::class) { origin("https://github.com/JetBrains/kotlin.git") }
          register("teamcity-achievements", GitVersionControlTarget::class) { origin("https://github.com/JetBrains/teamcity-achievements.git") }
          register("teamcity-commit-hooks", GitVersionControlTarget::class) { origin("https://github.com/JetBrains/teamcity-commit-hooks.git") }
          register("TeamCity.GitHubIssues", GitVersionControlTarget::class) { origin("https://github.com/JetBrains/TeamCity.GitHubIssues.git") }
          register("teamcity-google-agent", GitVersionControlTarget::class) { origin("https://github.com/JetBrains/teamcity-google-agent.git") }
          register("teamcity-local-cloud", GitVersionControlTarget::class) { origin("https://github.com/JetBrains/teamcity-local-cloud.git") }
          register("TeamCity.QueueManager", GitVersionControlTarget::class) { origin("https://github.com/JetBrains/TeamCity.QueueManager.git") }
          register("teamcity-sdk-maven-plugin", GitVersionControlTarget::class) { origin("https://github.com/JetBrains/teamcity-sdk-maven-plugin.git") }
        }
      }
      register("joel-costigliola") {
        vcs {
        }
      }
      register("johnrengelman") {
        vcs {
          register("shadow", GitVersionControlTarget::class) {
            origin("https://github.com/johnrengelman/shadow.git")
            remote("personal", "git@github.com:mkobit/shadow.git")
          }
        }
      }
      register("junit-team") {
        vcs {
          register("junit5", GitVersionControlTarget::class) { origin("https://github.com/junit-team/junit5.git") }
          register("junit5-samples", GitVersionControlTarget::class) { origin("https://github.com/junit-team/junit5-samples.git") }
        }
      }
      register("junit-pioneer") {
        vcs {
          register("junit-pioneer", GitVersionControlTarget::class) {
            origin("https://github.com/junit-pioneer/junit-pioneer.git")
            remote("personal", "git@github.com:mkobit/junit-pioneer.git")
          }
        }
      }
      register("Kotlin") {
        vcs {
          register("dokka", GitVersionControlTarget::class) { origin("https://github.com/Kotlin/dokka.git") }
          register("KEEP", GitVersionControlTarget::class) { origin("https://github.com/Kotlin/KEEP.git") }
          register("kotlinx.coroutines", GitVersionControlTarget::class) { origin("https://github.com/Kotlin/kotlinx.coroutines.git") }
        }
      }
      register("kubernetes") {
        vcs {
          register("autoscaler", GitVersionControlTarget::class) { origin("https://github.com/kubernetes/autoscaler.git") }
          register("charts", GitVersionControlTarget::class) { origin("https://github.com/kubernetes/charts.git") }
          register("helm", GitVersionControlTarget::class) { origin("https://github.com/kubernetes/helm.git") }
          register("kubernetes", GitVersionControlTarget::class) { origin("https://github.com/kubernetes/kubernetes.git") }
        }
      }
      register("mkobit") {
        vcs {
          register("android-app", GitVersionControlTarget::class) { origin("git@gitlab.com:ultimatepwner/android-app.git") }
          register("blog", GitVersionControlTarget::class) { origin("git@gitlab.com:mkobit/blog.git") }
          register("gradle-assertions", GitVersionControlTarget::class) { origin("git@github.com:mkobit/gradle-assertions.git") }
          register("gradle-junit-jupiter-extensions", GitVersionControlTarget::class) { origin("git@github.com:mkobit/gradle-junit-jupiter-extensions.git") }
          register("gradle-junit-platform-tools", GitVersionControlTarget::class) { origin("git@github.com:mkobit/gradle-junit-platform-tools.git") }
          register("gradle-test-kotlin-extensions", GitVersionControlTarget::class) { origin("git@github.com:mkobit/gradle-test-kotlin-extensions.git") }
          register("jenkins-pipeline-shared-libraries-gradle-plugin", GitVersionControlTarget::class) { origin("git@github.com:mkobit/jenkins-pipeline-shared-libraries-gradle-plugin.git") }
          register("jenkins-pipeline-shared-library-example", GitVersionControlTarget::class) { origin("git@github.com:mkobit/jenkins-pipeline-shared-library-example.git") }
          register("jenkins-scripts", GitVersionControlTarget::class) { origin("git@github.com:mkobit/jenkins-scripts.git") }
          register("junit5-dynamodb-local-extension", GitVersionControlTarget::class) { origin("git@github.com:mkobit/junit5-dynamodb-local-extension.git") }
          register("python-envs-gradle-plugin", GitVersionControlTarget::class) { origin("git@github.com:mkobit/toolchains-gradle-plugin.git") }
        }
      }
      register("mesonbuild") {
        vcs {
          register("meson", GitVersionControlTarget::class) { origin("https://github.com/mesonbuild/meson.git") }
        }
      }
      register("ratpack") {
        vcs {
          register("ratpack", GitVersionControlTarget::class) { origin("https://github.com/ratpack/ratpack.git") }
        }
      }
      register("robfletcher") {
        vcs {
          register("strikt", GitVersionControlTarget::class) {
            origin("https://github.com/robfletcher/strikt.git")
            remote("personal", "git@github.com:mkobit/strikt.git")
          }
        }
      }
      register("salesforce") {
        vcs {
          register("grpc-java-contrib", GitVersionControlTarget::class) { origin("https://github.com/salesforce/grpc-java-contrib.git") }
        }
      }
      register("square") {
        vcs {
          register("javapoet", GitVersionControlTarget::class) { origin("https://github.com/square/javapoet.git") }
          register("kotlinpoet", GitVersionControlTarget::class) { origin("https://github.com/square/kotlinpoet.git") }
          register("okhttp", GitVersionControlTarget::class) { origin("https://github.com/square/okhttp.git") }
          register("retrofit", GitVersionControlTarget::class) { origin("https://github.com/square/retrofit.git") }
        }
      }
      register("willowtreeapps") {
        vcs {
          register("assertk", GitVersionControlTarget::class) { origin("https://github.com/willowtreeapps/assertk.git") }
        }
      }
    }
  }
}

tasks {
  dependencyUpdates {
    val rejectPatterns = listOf("alpha", "beta", "rc", "cr", "m").map { qualifier ->
      Regex("(?i).*[.-]$qualifier[.\\d-]*")
    }
    resolutionStrategy {
      componentSelection {
        all {
          if (rejectPatterns.any { it.matches(this.candidate.version) }) {
            reject("Release candidate")
          }
        }
      }
    }
  }

  wrapper {
    gradleVersion = "5.5.1"
  }

  val personalWorkspace by creating(Mkdir::class) {
    directory.set(personalWorkspaceDirectory)
  }

  val workWorkspace by creating(Mkdir::class) {
    directory.set(workWorkspaceDirectory)
  }

  val codeLabWorkspace by creating(Mkdir::class) {
    directory.set(codeLabWorkspaceDirectory)
  }

  val workspace by registering {
    group = "Workspace"
    dependsOn(personalWorkspace, workWorkspace, codeLabWorkspace)
  }

  val screenRc by registering(Symlink::class) {
    source.set(projectFile("screen/screenrc.dotfile"))
    destination.set(locations.home.file(".screenrc"))
  }

  val screen by registering {
    group = "Screen"
    dependsOn(screenRc)
  }

  val tmuxConf by registering(Symlink::class) {
    source.set(projectFile("tmux/tmux.conf.dotfile"))
    destination.set(locations.home.file(".tmux.conf"))
  }

  val sshCms by registering(Mkdir::class) {
    directory.set(locations.home.dir(".ssh/controlMaster"))
  }

  val ssh by registering {
    group = "SSH"
    dependsOn(sshCms)
  }

  val tmux by registering {
    group = "Tmux"
    dependsOn(tmuxConf)
  }

  val vimRc by registering(Symlink::class) {
    source.set(projectFile("vim/vimrc.dotfile"))
    destination.set(locations.home.file(".vimrc"))
  }

  val vim by registering {
    group = "VIM"
    dependsOn(vimRc)
  }

  val generateZshrcFile by existing
  val zsh by registering {
    group = "ZSH"
    description = "Sets up ZSH"
    dependsOn(generateZshrcFile)
  }

  dotfiles {
    dependsOn(screen, ssh, tmux, vim, workspace, zsh)
  }
}
