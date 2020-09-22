import dotfilesbuild.dependencies.defaultDotfilesRepositories
import dotfilesbuild.home
import dotfilesbuild.io.git.GitVersionControlTarget

plugins {
  id("com.github.ben-manes.versions") version "0.33.0"
  id("org.jlleitschuh.gradle.ktlint") version "9.4.0"
  id("org.jetbrains.gradle.plugin.idea-ext") version "0.9" apply false

  dotfilesbuild.`self-update`
  dotfilesbuild.`vcs-management`
  dotfilesbuild.`git-vcs`
}

buildScan {
  termsOfServiceUrl = "https://gradle.com/terms-of-service"
  termsOfServiceAgree = "yes"
}

description = "Dotfiles and package management"

val workspace = home.dir("Workspace")
val personalWorkspaceDirectory: Directory = workspace.dir("personal")
val workWorkspaceDirectory: Directory = workspace.dir("work")
val codeLabWorkspaceDirectory: Directory = workspace.dir("code_lab")

ktlint {
  version.set("0.39.0")
}

repositories.defaultDotfilesRepositories()

// IntelliJ Regex:
// ^(\w+[:@/]+\w+.com[:/]?([\w\d-]+)/([\w\d-\.]+)\.git)$
// "$3"(GitVersionControlTarget::class) { origin("$1") }
versionControlTracking {
//  register("personal") {
//    directory.set(personalWorkspaceDirectory)
//    groups {
//      register("arrow-kt") {
//        vcs {
//          register("arrow", GitVersionControlTarget::class) { origin("https://github.com/arrow-kt/arrow.git") }
//        }
//      }
//      register("bazelbuild") {
//        vcs {
//          register("bazel", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/bazel.git") }
//          register("bazel-blog", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/bazel-blog.git") }
//          register("bazel-skylib", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/bazel-skylib.git") }
//          register("intellij", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/intellij.git") }
//          register("rules_go", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/rules_go.git") }
//          register("rules_kotlin", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/rules_kotlin.git") }
//          register("rules_webtesting", GitVersionControlTarget::class) { origin("https://github.com/bazelbuild/rules_webtesting.git") }
//        }
//      }
//      register("buildkite") {
//        vcs {
//          register("agent", GitVersionControlTarget::class) { origin("https://github.com/buildkite/agent.git") }
//        }
//      }
//      register("cloudbees") {
//        vcs {
//          register("groovy-cps", GitVersionControlTarget::class) { origin("https://github.com/cloudbees/groovy-cps.git") }
//          register("jenkins-scripts", GitVersionControlTarget::class) { origin("https://github.com/cloudbees/jenkins-scripts.git") }
//        }
//      }
//      register("ethereum") {
//        vcs {
//          register("ethereumj", GitVersionControlTarget::class) { origin("https://github.com/ethereum/ethereumj.git") }
//          register("go-ethereum", GitVersionControlTarget::class) { origin("https://github.com/ethereum/go-ethereum.git") }
//          register("pyethereum", GitVersionControlTarget::class) { origin("https://github.com/ethereum/pyethereum.git") }
//          register("solidity", GitVersionControlTarget::class) { origin("https://github.com/ethereum/solidity.git") }
//          register("wiki", GitVersionControlTarget::class) { origin("https://github.com/ethereum/wiki.git") }
//          register("wiki.wiki", GitVersionControlTarget::class) { origin("https://github.com/ethereum/wiki.wiki.git") }
//        }
//      }
//      register("google") {
//        vcs {
//          register("copybara", GitVersionControlTarget::class) { origin("https://github.com/google/copybara.git") }
//          register("protobuf-gradle-plugin", GitVersionControlTarget::class) {
//            origin("https://github.com/google/protobuf-gradle-plugin.git")
//            remote("personal", "git@github.com:mkobit/protobuf-gradle-plugin.git")
//          }
//        }
//      }
//      register("gradle") {
//        vcs {
//          register("gradle", GitVersionControlTarget::class) {
//            origin("https://github.com/gradle/gradle.git")
//            remote("personal", "git@github.com:mkobit/gradle.git")
//          }
//          register("gradle-completion", GitVersionControlTarget::class) { origin("https://github.com/gradle/gradle-completion.git") }
//          register("gradle-profiler", GitVersionControlTarget::class) { origin("https://github.com/gradle/gradle-profiler.git") }
//          register("kotlin-dsl", GitVersionControlTarget::class) {
//            origin("https://github.com/gradle/kotlin-dsl.git")
//            remote("personal", "git@github.com:mkobit/kotlin-dsl.git")
//          }
//        }
//      }
//      register("grpc") {
//        vcs {
//          register("grpc", GitVersionControlTarget::class) { origin("https://github.com/grpc/grpc.git") }
//          register("grpc-java", GitVersionControlTarget::class) { origin("https://github.com/grpc/grpc-java.git") }
//          register("grpc-go", GitVersionControlTarget::class) { origin("https://github.com/grpc/grpc-go.git") }
//        }
//      }
//      register("jacoco") {
//        vcs {
//          register("jacoco", GitVersionControlTarget::class) { origin("https://github.com/jacoco/jacoco.git") }
//        }
//      }
//      register("JetBrains") {
//        vcs {
//          // register("kotlin", GitVersionControlTarget::class) { origin("https://github.com/JetBrains/kotlin.git") }
//        }
//      }
//      register("junit-team") {
//        vcs {
//          register("junit5", GitVersionControlTarget::class) { origin("https://github.com/junit-team/junit5.git") }
//          register("junit5-samples", GitVersionControlTarget::class) { origin("https://github.com/junit-team/junit5-samples.git") }
//        }
//      }
//      register("junit-pioneer") {
//        vcs {
//          register("junit-pioneer", GitVersionControlTarget::class) {
//            origin("https://github.com/junit-pioneer/junit-pioneer.git")
//            remote("personal", "git@github.com:mkobit/junit-pioneer.git")
//          }
//        }
//      }
//      register("Kotlin") {
//        vcs {
//          register("dokka", GitVersionControlTarget::class) { origin("https://github.com/Kotlin/dokka.git") }
//          register("KEEP", GitVersionControlTarget::class) { origin("https://github.com/Kotlin/KEEP.git") }
//          register("kotlinx.coroutines", GitVersionControlTarget::class) { origin("https://github.com/Kotlin/kotlinx.coroutines.git") }
//        }
//      }
//      register("kubernetes") {
//        vcs {
//          register("autoscaler", GitVersionControlTarget::class) { origin("https://github.com/kubernetes/autoscaler.git") }
//          register("charts", GitVersionControlTarget::class) { origin("https://github.com/kubernetes/charts.git") }
//          register("helm", GitVersionControlTarget::class) { origin("https://github.com/kubernetes/helm.git") }
//          register("kubernetes", GitVersionControlTarget::class) { origin("https://github.com/kubernetes/kubernetes.git") }
//        }
//      }
//      register("mkobit") {
//        vcs {
//          register("blog", GitVersionControlTarget::class) { origin("git@gitlab.com:mkobit/blog.git") }
//          register("gradle-assertions", GitVersionControlTarget::class) { origin("git@github.com:mkobit/gradle-assertions.git") }
//          register("gradle-junit-jupiter-extensions", GitVersionControlTarget::class) { origin("git@github.com:mkobit/gradle-junit-jupiter-extensions.git") }
//          register("gradle-junit-platform-tools", GitVersionControlTarget::class) { origin("git@github.com:mkobit/gradle-junit-platform-tools.git") }
//          register("gradle-test-kotlin-extensions", GitVersionControlTarget::class) { origin("git@github.com:mkobit/gradle-test-kotlin-extensions.git") }
//          register("jenkins-pipeline-shared-libraries-gradle-plugin", GitVersionControlTarget::class) { origin("git@github.com:mkobit/jenkins-pipeline-shared-libraries-gradle-plugin.git") }
//          register("jenkins-pipeline-shared-library-example", GitVersionControlTarget::class) { origin("git@github.com:mkobit/jenkins-pipeline-shared-library-example.git") }
//          register("jenkins-scripts", GitVersionControlTarget::class) { origin("git@github.com:mkobit/jenkins-scripts.git") }
//          register("junit5-dynamodb-local-extension", GitVersionControlTarget::class) { origin("git@github.com:mkobit/junit5-dynamodb-local-extension.git") }
//          register("python-envs-gradle-plugin", GitVersionControlTarget::class) { origin("git@github.com:mkobit/toolchains-gradle-plugin.git") }
//        }
//      }
//      register("mesonbuild") {
//        vcs {
//          register("meson", GitVersionControlTarget::class) { origin("https://github.com/mesonbuild/meson.git") }
//        }
//      }
//      register("robfletcher") {
//        vcs {
//          register("strikt", GitVersionControlTarget::class) {
//            origin("https://github.com/robfletcher/strikt.git")
//            remote("personal", "git@github.com:mkobit/strikt.git")
//          }
//        }
//      }
//      register("salesforce") {
//        vcs {
//          register("grpc-java-contrib", GitVersionControlTarget::class) { origin("https://github.com/salesforce/grpc-java-contrib.git") }
//        }
//      }
//      register("square") {
//        vcs {
//          register("javapoet", GitVersionControlTarget::class) { origin("https://github.com/square/javapoet.git") }
//          register("kotlinpoet", GitVersionControlTarget::class) { origin("https://github.com/square/kotlinpoet.git") }
//          register("okhttp", GitVersionControlTarget::class) { origin("https://github.com/square/okhttp.git") }
//          register("retrofit", GitVersionControlTarget::class) { origin("https://github.com/square/retrofit.git") }
//        }
//      }
//    }
//  }
}

tasks {
  dependencyUpdates {
    val rejectPatterns = listOf("alpha", "beta", "rc", "cr", "m").map { qualifier ->
      Regex("(?i).*[.-]$qualifier[.\\d-]*")
    }
    resolutionStrategy {
      componentSelection {
        all {
          if (rejectPatterns.any { it.matches(candidate.version) }) {
            reject("Release candidate")
          }
        }
      }
    }
  }

  wrapper {
    gradleVersion = "6.6.1"
  }
}
