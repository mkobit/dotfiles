import dotfilesbuild.dependencies.defaultDotfilesRepositories
import dotfilesbuild.home

plugins {
  id("com.github.ben-manes.versions") version "0.36.0"
  id("org.jlleitschuh.gradle.ktlint") version "9.4.0"
  id("org.jetbrains.gradle.plugin.idea-ext") version "0.10" apply false
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
    gradleVersion = "6.8"
  }
}
