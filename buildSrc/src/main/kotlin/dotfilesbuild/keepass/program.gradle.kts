package dotfilesbuild.keepass

import dotfilesbuild.io.file.EditFile
import dotfilesbuild.io.file.content.SetContent
import dotfilesbuild.io.http.Download

plugins {
  id("dotfilesbuild.dotfiles-lifecycle")
}

val taskGroup = "KeePass"

val keepass = extensions.create(
  "keepass",
  KeepassExtension::class,
  objects.property<String>(),
  objects.fileProperty()
)

val keepassDirectory = layout.buildDirectory.dir("keepass")
val versionDirectory = keepassDirectory.flatMap {
  it.dir(keepass.keepassVersion.map { version -> "KeePass-$version" })
}
val installDirectory = versionDirectory.map { it.dir("installation") }

tasks {
  val downloadKeepassZip = register("downloadKeepassZip", Download::class) {
    description = "Downloads the KeePass ZIP distribution"
    group = taskGroup
    url.set(
      keepass.keepassVersion.map { version ->
        "https://sourceforge.net/projects/keepass/files/KeePass ${version[0]}.x/$version/KeePass-$version.zip/download"
      }
    )
    destination.set(
      versionDirectory.flatMap {
        it.file(keepass.keepassVersion.map { version -> "KeePass-$version.zip" })
      }
    )
  }

  val extractKeePassZip by registering(Copy::class) {
    description = "Extracts the KeePass ZIP distribution"
    group = taskGroup
    from(
      downloadKeepassZip
        .flatMap { it.destination }
        .map { zipTree(it) }
    )
    into(installDirectory)
  }

  val generateKeePassExecutable by registering(EditFile::class) {
    description = "Generate executable file that runs KeePass using mono"
    group = taskGroup
    editActions.add(
      SetContent {
        """
          #!/usr/bin/env bash
          set -euo pipefail
          
          nohup mono ${installDirectory.map { "$it/KeePass.exe" }.get()} /home/mkobit/Programs/kobit.kdbx > ${versionDirectory.map { it.file("output.log") }.get()} 2>&1 & disown
        """.trimIndent()
      }
    )
    file.set(versionDirectory.map { it.file("keepass") })
    executable.set(true)
  }

  "dotfiles" {
    dependsOn(extractKeePassZip, generateKeePassExecutable)
  }
}
