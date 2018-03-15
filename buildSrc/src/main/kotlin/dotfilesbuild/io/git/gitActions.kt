package dotfilesbuild.io.git

import mu.KotlinLogging
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
//    Git.cloneRepository()
//        .setRemote("origin")
//        .setURI(remoteUrl)
//        .setDirectory(directory)
//        .call().use {
//      LOGGER.info { "Cloned $directory to $remoteUrl" }
//    }
  }
}

class FetchAction @Inject constructor(
    private val repository: File
) : Runnable {
  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  override fun run() {
//    Git.open(repository).use {
//      it.fetch()
//          .setRemote("origin")
//          .call()
//      LOGGER.info { "Fetched origin for $repository" }
//    }
  }
}

class PullAction @Inject constructor(
    private val repository: File
) : Runnable {
  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  override fun run() {
//    Git.open(repository).use {
//      it.pull()
//          .setRebase(true)
//          .setRemote("origin")
//          .call()
//      LOGGER.info { "Pulled origin for $repository" }
//    }
  }
}
