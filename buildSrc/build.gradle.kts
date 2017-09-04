plugins {
  `java-library`
  kotlin("jvm")
  // TODO: wait until next release to work properly
//  `kotlin-dsl`
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
  implementation(kotlin("stdlib-jre8"))
  implementation("io.github.microutils:kotlin-logging:1.4.6")
  implementation("org.eclipse.jgit:org.eclipse.jgit:4.8.0.201706111038-r")
}
