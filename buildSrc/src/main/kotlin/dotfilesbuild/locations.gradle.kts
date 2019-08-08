package dotfilesbuild

plugins {
  base
}

val userHome: String = System.getProperty("user.home")
val homeDirectory: Directory = objects.directoryProperty().let {
  it.set(file(userHome))
  it.get()
}

val home = LocationsExtension(
  homeDirectory,
  homeDirectory.dir("Workspace"),
  homeDirectory.dir("Programs"),
  homeDirectory.dir("Downloads"),
  layout.buildDirectory.dir("managed"),
  layout.projectDirectory.dir(".unmanaged")
)

extensions.add(
  LocationsExtension::class,
  "locations",
  home
)
