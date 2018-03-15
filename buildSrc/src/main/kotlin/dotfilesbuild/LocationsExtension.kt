package dotfilesbuild

import org.gradle.api.file.Directory

class LocationsExtension(
    val home: Directory,
    val workspace: Directory,
    val programs: Directory,
    val downloads: Directory
)
