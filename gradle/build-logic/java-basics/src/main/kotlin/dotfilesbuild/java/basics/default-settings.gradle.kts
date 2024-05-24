package dotfilesbuild.java.basics

plugins {
  java
  `jvm-test-suite`
}

java {
  toolchain {
    languageVersion = JavaLanguageVersion.of(21)
  }
}

testing {
  suites {
    withType<JvmTestSuite> {
      useJUnitJupiter()
      dependencies {
        implementation(platform("org.junit:junit-bom:5.10.2"))
        implementation("org.junit.jupiter:junit-jupiter-params")
        implementation("org.junit.jupiter:junit-jupiter-api")

        runtimeOnly("org.junit.jupiter:junit-jupiter-engine")
        runtimeOnly("org.junit.platform:junit-platform-runner")
      }
    }
  }
}
