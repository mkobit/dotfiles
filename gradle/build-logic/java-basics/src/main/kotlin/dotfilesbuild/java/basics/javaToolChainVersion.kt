package dotfilesbuild.java.basics

import org.gradle.jvm.toolchain.JavaLanguageVersion
import org.gradle.jvm.toolchain.JavaToolchainSpec
import org.gradle.jvm.toolchain.JvmVendorSpec

fun JavaToolchainSpec.applyDefaultJavaToolchainConfiguration() {
  vendor.set(JvmVendorSpec.ADOPTIUM)
  languageVersion.set(JavaLanguageVersion.of(21))
}
