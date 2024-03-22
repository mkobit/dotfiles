rootProject.name = "build-logic-settings"

dependencyResolutionManagement {
  repositories {
    mavenCentral()
  }
}

apply(from = file("../gradle/buildCache.settings.gradle.kts"))

include("dotfiles-version-catalog")
