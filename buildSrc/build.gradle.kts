import org.gradle.kotlin.dsl.`embedded-kotlin`
import org.jetbrains.kotlin.gradle.dsl.Coroutines

plugins {
  `java-library`
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

val coroutinesVersion by extra { "0.21" }

dependencies {
  val arrowVersion = "0.5.4"
//  implementation(kotlin("stdlib-jre8"))
  implementation("io.arrow-kt:arrow-core:$arrowVersion")
  implementation("io.arrow-kt:arrow-typeclasses:$arrowVersion")
  implementation("io.arrow-kt:arrow-instances:$arrowVersion")
  implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:$coroutinesVersion")
  implementation("com.squareup.retrofit2:retrofit:2.3.0")
  implementation("com.squareup.okhttp3:okhttp:3.9.0")
  implementation("io.github.microutils:kotlin-logging:1.4.9")
  implementation("org.eclipse.jgit:org.eclipse.jgit:4.10.0.201712302008-r")
}

kotlin {
  experimental.coroutines = Coroutines.ENABLE
}
