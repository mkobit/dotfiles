rootProject.buildFileName = "buildSrc.gradle.kts"

dependencyResolutionManagement {
  repositories {
    mavenCentral()
    jcenter()
  }
}

apply(from = file("../gradle/buildCache.settings.gradle.kts"))
