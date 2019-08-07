package dotfilesbuild.intellij

import dotfilesbuild.io.file.EditFile
import dotfilesbuild.io.file.content.SetContent
import dotfilesbuild.io.http.Download

plugins {
  id("dotfilesbuild.dotfiles-lifecycle")
}

val taskGroup = "IntelliJ"

val intellij = extensions.create(
  "intellij",
  IntelliJExtension::class,
  objects.property<String>(),
  objects.property<Distribution>().apply {
    set(Distribution.ULTIMATE)
  }
)

val intellijDirectory = layout.buildDirectory.dir("intellij")
val versionDirectory = intellijDirectory.flatMap {
  it.dir(
    intellij.intellijVersion.flatMap { version ->
      intellij.distributionType.map { distribution ->
        "IntelliJ-$distribution-$version"
      }
    }
  )
}
val installDirectory = versionDirectory.map { it.dir("installation") }

tasks {
  val downloadIntellijZip by registering(Download::class) {
    description = "Downloads the IntelliJ ZIP distribution"
    group = taskGroup
    url.set(intellij.intellijVersion.flatMap { version ->
      intellij.distributionType.map { type ->
        "https://download.jetbrains.com/idea/idea${type.code}-$version.tar.gz"
      }
    })

    destination.set(
      versionDirectory.flatMap { directory ->
        intellij.intellijVersion.flatMap { version ->
          intellij.distributionType.map { type ->
            directory.file("idea${type.code}-$version.tar.gz")
          }
        }
      }
    )
  }

  // TODO: never up to date for some stupid reason
  val extractIntellijZip by registering(Copy::class) {
    description = "Extracts the IntelliJ ZIP distribution"
    group = taskGroup
    from(
      downloadIntellijZip
        .flatMap { it.destination }
        .map { tarTree(it) }
    )
    into(installDirectory)
  }

  val generateIntelliJExecutable by registering(EditFile::class) {
    description = "Generate executable file that runs KeePass using mono"
    group = taskGroup
    editActions.add(
      SetContent {
        """
          #!/usr/bin/env bash
          set -euo pipefail
          readonly intellij_home=$(ls -1 "${installDirectory.get()}" | head -n 1)
          nohup mono "${'$'}{intellij_home}" > ${versionDirectory.map { it.file("output.log") }.get()} 2>&1 & disown
        """.trimIndent()
      }
    )
    file.set(versionDirectory.map { it.file("intellij") })
    executable.set(true)
  }

  "dotfiles" {
    dependsOn(extractIntellijZip, generateIntelliJExecutable)
  }
}
