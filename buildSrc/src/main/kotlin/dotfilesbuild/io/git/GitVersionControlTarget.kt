package dotfilesbuild.io.git

import dotfilesbuild.io.vcs.VersionControlTarget

data class GitVersionControlTarget(
    private val repositoryName: String,
    var remotes: Map<String, String>
) : VersionControlTarget {

  override fun getName(): String = repositoryName

  fun remote(name: String, url: String) {
    remotes += mapOf(name to url)
  }

  fun origin(url: String) {
    remotes += mapOf("origin" to url)
  }
}
