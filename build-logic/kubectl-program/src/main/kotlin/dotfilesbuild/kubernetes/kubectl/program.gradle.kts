package dotfilesbuild.kubernetes.kubectl

import dotfilesbuild.io.http.Download

plugins {
  base
}

val executable by configurations.creating {
  isCanBeConsumed = true
  isCanBeResolved = false
  attributes {
    attribute(Usage.USAGE_ATTRIBUTE, objects.named(Usage::class, "executable"))
  }
}

val bin by configurations.creating {
  isCanBeConsumed = true
  isCanBeResolved = false
  attributes {
    attribute(Usage.USAGE_ATTRIBUTE, objects.named(Usage::class, "bin"))
  }
}

val kubectl = extensions.create<KubectlProgramExtension>("kubectl", objects.property<String>())
val binDir = layout.buildDirectory.file("bin/kubectl")

val downloadKubeCtl by tasks.registering(Download::class) {
  description = "Download kubectl and make it executable"
  url.set(
    kubectl.version.map {
      "https://storage.googleapis.com/kubernetes-release/release/$it/bin/linux/amd64/kubectl" // TODO: determine arch before download
    }
  )
  destination.set(binDir)
  executable.set(true)
}

executable.outgoing.artifact(downloadKubeCtl.map { it.destination }.get()) {
  builtBy(downloadKubeCtl)
}

bin.outgoing.artifact(downloadKubeCtl.map { task -> task.destination.asFile.get().parentFile }) {
  builtBy(downloadKubeCtl)
}
