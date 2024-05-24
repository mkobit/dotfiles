dependencyResolutionManagement {
  repositories {
    mavenCentral()
  }
}

buildCache {
  local {
    removeUnusedEntriesAfterDays = 90
  }
}
