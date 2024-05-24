plugins {
  `kotlin-dsl`
}

dependencies {
  implementation(projects.common)
  implementation(projects.javaBasics)
  implementation(libs.plugins.kotlin.jvm.map { it.toMarkerDependency() })
  implementation(libs.plugins.kotlin.multiplatform.map { it.toMarkerDependency() })
}

private fun PluginDependency.toMarkerDependency(): String =
  "${pluginId}:${pluginId}.gradle.plugin:${version}"
