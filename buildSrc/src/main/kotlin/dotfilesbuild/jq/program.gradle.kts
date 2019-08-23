package dotfilesbuild.jq

import dotfilesbuild.io.file.CalculateChecksum
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
  objects.property<String>(),
  objects.property<String>()
)

val jqVersionDirectory = layout.buildDirectory.dir("jq").flatMap { dir ->
  dir.dir(jq.jqVersion.map { version -> "$version/bin/jq" })
}
val taskGroup = "jq"
val distribution = "jq-linux64"

val downloadJq by tasks.registering(Download::class) {
  group = taskGroup
  description = "Downloads jq distribution"
  url.set(
    jq.jqVersion.map { "https://github.com/stedolan/jq/releases/download/jq-$it/$distribution" }
  )
  destination.set(
    jqVersionDirectory.map { dir ->
      dir.file("bin/jq")
    }
  )
  executable.set(true)
}

val checksumJq by tasks.registering(CalculateChecksum::class) {
  group = taskGroup
  description = "Calculates checksum for jq binary"
  digestFiles.from(downloadJq.flatMap { it.destination })
  checksums.set(
    jqVersionDirectory.map { dir ->
      dir.dir("checksums")
    }
  )
}

val downloadOfficialJqChecksum by tasks.registering(Download::class) {
  group = taskGroup
  description = "Downloads official jq SHA file"
  val downloadSha = "2e01ff1fb69609540b2bdc4e62a60499f2b2fb8e"
  url.set(
    jq.jqVersion.map { "https://raw.githubusercontent.com/stedolan/jq/$downloadSha/sig/v$it/sha256sum.txt" }
  )
  destination.set(
    jqVersionDirectory.map { dir ->
      dir.file("release-checksums/sha256sum.txt")
    }
  )
}

val assertChecksums by tasks.registering {
  group = taskGroup
  description = "Verifies downloaded checksum with locally calculated one"
  inputs.files(checksumJq.flatMap { it.checksums }).withPropertyName("calculated checksums")
  inputs.file(downloadOfficialJqChecksum.flatMap { it.destination }).withPropertyName("official checksums")
  doFirst("assert checksums are the same") {
    val calculated = checksumJq.flatMap { it.checksums }
      .map { it.asFileTree.singleFile }
      .get()
      .readText()
    val (officialSha, binary) = downloadOfficialJqChecksum
      .flatMap { it.destination }
      .map { it.asFile }
      .get()
      .let { file ->
        file.readLines()
          .map { it.split(Regex("\\s+"), 2) }
          .first { (_, binaryName) -> binaryName == distribution }
      }
    if (calculated != officialSha) {
      throw GradleException("Calculated SHA $calculated not equal to binary $distribution")
    }
  }
}

bin.outgoing.artifact(downloadJq.flatMap { task -> task.destination }.map { it.asFile.parentFile }) {
  builtBy(assertChecksums)
}
