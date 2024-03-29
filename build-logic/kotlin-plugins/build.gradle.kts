plugins {
  `kotlin-dsl`
}

dependencies {
  // https://github.com/gradle/gradle/issues/9282
  fun gradlePlugin(id: String, version: String): String = "$id:$id.gradle.plugin:$version"
  implementation(gradlePlugin("org.jetbrains.kotlin.jvm", "1.9.22"))

  // hack to make catalog available in precompiled scripts
  // see https://github.com/gradle/gradle/issues/15383
  implementation(files(libs.javaClass.superclass.protectionDomain.codeSource.location))
  implementation(files(testLibs.javaClass.superclass.protectionDomain.codeSource.location))
}
