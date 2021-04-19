plugins {
  `version-catalog`
}

catalog {
  versionCatalog {
    buildLibs()
  }
}

// need versions available in:
// subprojects/my-sub/mySub.gradle.kts (subproject build)
//  - needs root settings.gradle.kts
//  - settings plugin
// build-logic/kotlin-library-convention-plugin/src/dotfilesbuild.kotlin-library-convention.gradle.kts (convention plugin)
//  - needs plugins {} block
//  - project plugin
