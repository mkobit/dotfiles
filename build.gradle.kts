plugins {
  alias(libs.plugins.versions)
//  id("org.jetbrains.gradle.plugin.idea-ext") version "1.1.1" apply false
//  id("dotfilesbuild.dotfiles-lifecycle") // todo: propbably should be removed
}

description = "Dotfiles and package management"
//
//val workspace = home.dir("Workspace")
//val personalWorkspaceDirectory: Directory = workspace.dir("personal")
//val workWorkspaceDirectory: Directory = workspace.dir("work")
//val codeLabWorkspaceDirectory: Directory = workspace.dir("code_lab")

// val ktlintVersion = "0.41.0"
// ktlint {
//  version.set(ktlintVersion)
// }

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
    gradleVersion = "8.7"
  }
}
