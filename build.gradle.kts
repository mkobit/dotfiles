import dotfilesbuild.dependencies.defaultDotfilesRepositories
import dotfilesbuild.home

plugins {
  id("com.github.ben-manes.versions") version "0.36.0"
  id("org.jlleitschuh.gradle.ktlint") version "10.0.0"
  id("org.jetbrains.gradle.plugin.idea-ext") version "1.0" apply false
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

val ktlintVersion = "0.40.0"
ktlint {
  version.set(ktlintVersion)
}

subprojects {
  plugins.withId("org.jlleitschuh.gradle.ktlint") {
    the<org.jlleitschuh.gradle.ktlint.KtlintExtension>().version.set(ktlintVersion)
  }
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
    gradleVersion = "6.8.3"
  }
}
