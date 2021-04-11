package dotfilesbuild.dependencies

import org.gradle.api.artifacts.dsl.RepositoryHandler

fun RepositoryHandler.defaultDotfilesRepositories() {
  mavenCentral()
  jcenter()
}
