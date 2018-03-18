package dotfilesbuild.io.git

import mu.KotlinLogging
import org.eclipse.jgit.api.Git
import java.io.File
import javax.inject.Inject

class CloneAction @Inject constructor(
    private val directory: File,
    private val remoteUrl: String
) : Runnable {
  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  override fun run() {
    Git.cloneRepository()
        .setRemote("origin")
        .setURI(remoteUrl)
        .setDirectory(directory)
        .call().use {
      LOGGER.info { "Cloned $directory to $remoteUrl" }
    }
  }
}

class FetchAction @Inject constructor(
    private val repository: File,
    private val remote: String
) : Runnable {
  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  override fun run() {
    Git.open(repository).use {
      it.fetch()
          .setRemote(remote)
          .call()
      LOGGER.info { "Fetched origin for $repository" }
    }
  }
}

class PullAction @Inject constructor(
    private val repository: File,
    private val remote: String
) : Runnable {
  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  override fun run() {
    Git.open(repository).use {
      it.pull()
          .setRebase(true)
          .setRemote(remote)
          .call()
      LOGGER.info { "Pulled origin for $repository" }
    }
  }
}
