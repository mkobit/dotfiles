package dotfilesbuild

import org.gradle.api.file.Directory
import org.gradle.api.provider.Provider

/**
 * Different locations for files.
 * @property home the user home directory
 * @property workspace the code workspace directory
 * @property programs the directory for other programs
 * @property downloads the directory for downloading files
 * @property managed locations of files that are totally managed by build lifecycle and will be purged on `clean`
 * @property unmanaged locations of files that are partially managed by build lifecycle and will not be purged on `clean`
 */
class LocationsExtension(
  val home: Directory,
  val workspace: Directory,
  val programs: Directory,
  val downloads: Directory,
  val managed: Provider<Directory>,
  val unmanaged: Directory
)
