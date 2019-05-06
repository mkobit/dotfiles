package dotfilesbuild.io.git

import dotfilesbuild.io.vcs.VersionControlTarget
import org.gradle.api.file.Directory
import org.gradle.api.provider.Provider

data class GitVersionControlTarget(
  private val repositoryName: String,
  var remotes: Map<String, String>,
  override val directory: Provider<Directory>
) : VersionControlTarget {

  init {
    require(repositoryName.trim() == repositoryName) {
      "repositoryName '$name' must not begin or start with whitespace"
    }
  }

  override fun getName(): String = repositoryName

  fun remote(name: String, url: String) {
    require(name.trim() == name) { "remote name '$name' must not begin or end with whitespace" }
    require(url.trim() == url) { "remote url '$url' must not begin or end with whitespace" }
    remotes += name to url
  }

  fun origin(url: String) = remote("origin", url)
}
