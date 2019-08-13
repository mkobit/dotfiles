import dotfilesbuild.dependencies.guava
import dotfilesbuild.dependencies.jacksonCore
import dotfilesbuild.dependencies.jacksonModule
import dotfilesbuild.dependencies.kotlinLogging
import dotfilesbuild.dependencies.kotlinxCoroutines
import dotfilesbuild.dependencies.picoCli
import dotfilesbuild.dependencies.useDotfilesDependencyRecommendations
import org.jetbrains.kotlin.gradle.plugin.KotlinSourceSet

plugins {
  id("org.jlleitschuh.gradle.ktlint")
  dotfilesbuild.kotlin.convention
  application
}

ktlint {
  version.set("0.32.0")
  filter {
//    exclude("**/generated-source/**") Don't know why this isn't working
    exclude("**/*")
  }
}

configurations.all {
  useDotfilesDependencyRecommendations()
}

dependencies {
  implementation(guava)
  implementation(picoCli)

  implementation(kotlin("stdlib-jdk8"))
  implementation(kotlinxCoroutines("core"))
  implementation(kotlinxCoroutines("jdk8"))

  implementation(kotlinLogging)
}


application {
  mainClassName = "dotfiles.note/com.mkobit.dotfiles.note.Main"
}
