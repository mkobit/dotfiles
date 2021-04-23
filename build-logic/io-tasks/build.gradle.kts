plugins {
  `kotlin-dsl`
}

dependencies {
  implementation(libs.kotlinLogging)
  implementation(libs.arrow.core)
  implementation(libs.okhttp.client)

  testImplementation(testLibs.mockk)

  testImplementation("com.mkobit.gradle.test:gradle-test-kotlin-extensions:0.8.0")
  testImplementation(testLibs.strikt.core)
  testImplementation(testLibs.strikt.gradle)
  testImplementation(testLibs.strikt.jvm)

  testImplementation(testLibs.minutest)
  testImplementation(testLibs.junit.jupiter.api)
  testImplementation(testLibs.junit.jupiter.params)

  testRuntimeOnly(testLibs.junit.jupiter.engine)
  testRuntimeOnly(testLibs.log4j.core)
  testRuntimeOnly(testLibs.log4j.jul)
}

tasks {
  test {
    useJUnitPlatform()
    systemProperty("java.util.logging.manager", "org.apache.logging.log4j.jul.LogManager")
  }
}
