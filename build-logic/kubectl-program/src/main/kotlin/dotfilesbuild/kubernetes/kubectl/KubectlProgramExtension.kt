package dotfilesbuild.kubernetes.kubectl

import org.gradle.api.provider.Property

open class KubectlProgramExtension(
  val version: Property<String>
)
