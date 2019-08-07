package dotfilesbuild.keepass

import dotfilesbuild.LocationsExtension
import dotfilesbuild.io.file.Symlink
import dotfilesbuild.io.http.Download

plugins {
  id("dotfilesbuild.locations")
}

val taskGroup = "KeePass"

val locations = extensions.getByType(LocationsExtension::class)

val keepass = extensions.create(
  "keepass",
  KeepassExtension::class,
  objects.property<String>(),
  objects.directoryProperty().apply {
    set(locations.downloads)
  },
  objects.directoryProperty().apply {
    set(locations.programs)
  }
)

val downloadKeepassZip = tasks.register("downloadKeepassZip", Download::class) {
  description = "Downloads the KeePass ZIP distribution"
  group = taskGroup
  destination.set(
    keepass.downloadDirectory.file(keepass.keepassVersion.map { version -> "KeePass-$version.zip" })
  )
  url.set(keepass.keepassVersion.map { version ->
    "https://sourceforge.net/projects/keepass/files/KeePass ${version[0]}.x/$version/KeePass-$version.zip/download"
  })
}

val installDirectoryForVersion = keepass.installDirectory.dir(keepass.keepassVersion.map { "KeePass-$it" })
val extractKeepassZip = tasks.register("extractKeepassZip", Copy::class) {
  description = "Extracts the KeePass ZIP distribution"
  group = taskGroup
  dependsOn(downloadKeepassZip)
  from(Callable { zipTree(downloadKeepassZip.map(Download::destination).get()) })
  into(installDirectoryForVersion)
}

tasks.register("symlinkKeePassProgram", Symlink::class) {
  description = "Creates a symlink to the KeePass directory"
  group = taskGroup
  dependsOn(extractKeepassZip)
  source.set(installDirectoryForVersion)
  destination.set(keepass.installDirectory.dir("keepass"))
}
