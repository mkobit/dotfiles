import org.gradle.api.artifacts.dsl.DependencyHandler

fun DependencyHandler.gradlePlugin(id: String, version: String): String = "$id:$id.gradle.plugin:$version"
