package dotfilesbuild

import org.gradle.api.file.Directory

/**
 * Different locations for files.
 * @property home the user home directory
 * @property workspace the code workspace directory
 * @property programs the directory for other programs
 * @property downloads the directory for downloading files
 */
class LocationsExtension(
  val home: Directory,
  val workspace: Directory,
  val programs: Directory,
  val downloads: Directory
)
