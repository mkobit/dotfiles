package dotfilesbuild.jq

import dotfilesbuild.io.http.Download

plugins {
  base
}

// Details from https://stedolan.github.io/jq/download/

val bin by configurations.creating {
  isCanBeConsumed = true
  isCanBeResolved = false
  attributes {
    attribute(Usage.USAGE_ATTRIBUTE, objects.named(Usage::class, "bin"))
  }
}

val jq = extensions.create(
  "jq",
  JqExtension::class,
  objects.property<String>()
)

val jqDirectory = layout.buildDirectory.dir("jq")

val downloadJq by tasks.registering(Download::class) {
  group = "jq"
  description = "Downloads jq distribution"
  url.set(
    jq.jqVersion.map { "https://github.com/stedolan/jq/releases/download/jq-$it/jq-linux64" }
  )
  destination.set(
    jqDirectory.flatMap { dir ->
      dir.file(
        jq.jqVersion.map { version -> "$version/jq" }
      )
    }
  )
  executable.set(true)
}

bin.outgoing.artifact(downloadJq.flatMap { task -> task.destination })
