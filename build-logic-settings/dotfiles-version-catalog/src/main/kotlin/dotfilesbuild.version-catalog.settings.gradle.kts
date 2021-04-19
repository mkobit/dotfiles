enableFeaturePreview("VERSION_CATALOGS")

dependencyResolutionManagement {
  versionCatalogs {
    create("libs") {
      buildLibs()
    }
    create("testLibs") {
      buildTestLibs()
    }
  }
}
