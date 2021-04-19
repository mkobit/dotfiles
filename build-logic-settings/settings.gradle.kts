rootProject.name = "build-logic-settings"

dependencyResolutionManagement {
  repositories {
    mavenCentral()
    jcenter()
  }
}

apply(from = file("../gradle/buildCache.settings.gradle.kts"))

include("dotfiles-version-catalog")
