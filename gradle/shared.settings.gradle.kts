dependencyResolutionManagement {
  repositories {
    mavenCentral()
    gradlePluginPortal()
  }
}

buildCache {
  local {
    removeUnusedEntriesAfterDays = 90
  }
}
