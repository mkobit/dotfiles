dependencyResolutionManagement {
  repositories {
    mavenCentral()
    jcenter()
  }
}

apply(from = file("../gradle/buildCache.settings.gradle.kts"))
