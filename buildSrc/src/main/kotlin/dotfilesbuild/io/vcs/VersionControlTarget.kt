package dotfilesbuild.io.vcs

import org.gradle.api.Named
import org.gradle.api.file.Directory
import org.gradle.api.provider.Provider

interface VersionControlTarget : Named {
  val directory: Provider<Directory>
}
