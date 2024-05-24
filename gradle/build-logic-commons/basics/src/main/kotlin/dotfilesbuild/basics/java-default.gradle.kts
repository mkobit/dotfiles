package dotfilesbuild.basics

plugins {
  java
}

java {
  toolchain {
    languageVersion = JavaLanguageVersion.of(21)
    vendor = JvmVendorSpec.ADOPTIUM
  }
}
