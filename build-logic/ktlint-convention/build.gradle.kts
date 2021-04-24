plugins {
  `kotlin-dsl`
}

dependencies {
  fun gradlePlugin(id: String, version: String): String = "$id:$id.gradle.plugin:$version"
  implementation(gradlePlugin("org.jlleitschuh.gradle.ktlint", "10.0.0"))
}
