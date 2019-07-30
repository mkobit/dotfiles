package dotfilesbuild.dependencies

import org.gradle.api.artifacts.dsl.RepositoryHandler
import org.gradle.kotlin.dsl.maven

fun RepositoryHandler.defaultDotfilesRepositories() {
  jcenter()
  mavenCentral()
}

fun RepositoryHandler.kotlinx() = maven(url = "https://dl.bintray.com/kotlin/kotlinx") {
  name = "kotlinx"
}
