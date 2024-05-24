plugins {
  id("org.gradle.toolchains.foojay-resolver-convention") version("0.8.0")
}

rootProject.name = "build-logic"

apply(from = file("../shared.settings.gradle.kts"))

dependencyResolutionManagement {
  versionCatalogs {
    create("libs") {
      from(files("../libs.versions.toml"))
    }
  }
}

include("basics")
include("common")
include("java-basics")
include("kotlin-basics")

enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")
