import org.gradle.kotlin.dsl.`embedded-kotlin`
import org.jetbrains.kotlin.gradle.dsl.Coroutines

plugins {
  `java-library`
//  kotlin("jvm") version "1.1.51"
  // TODO: wait until next release to work properly
//  `kotlin-dsl`
//  `embedded-kotlin`
  `kotlin-dsl`
  `java-gradle-plugin`
}

repositories {
  jcenter()
}

java {
  sourceCompatibility = JavaVersion.VERSION_1_8
  targetCompatibility = JavaVersion.VERSION_1_8
}

dependencies {
  implementation(gradleApi())
//  implementation(kotlin("stdlib-jre8"))
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines:0.19.1")
  implementation("com.squareup.retrofit2:retrofit:2.3.0")
  implementation("com.squareup.okhttp3:okhttp:3.9.0")
  implementation("io.github.microutils:kotlin-logging:1.4.6")
  implementation("org.eclipse.jgit:org.eclipse.jgit:4.8.0.201706111038-r")
}

kotlin {
  experimental.coroutines = Coroutines.ENABLE
}
