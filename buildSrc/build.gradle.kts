plugins {
  `java-library`
  `kotlin-dsl`
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
}
