package dotfilesbuild.io.git

import com.jcraft.jsch.Session
import mu.KotlinLogging
import org.eclipse.jgit.api.Git
import org.eclipse.jgit.transport.JschConfigSessionFactory
import org.eclipse.jgit.transport.OpenSshConfig
import org.eclipse.jgit.transport.SshTransport
import org.eclipse.jgit.transport.URIish
import java.io.File
import javax.inject.Inject

private val sessionConfigFactory = object : JschConfigSessionFactory() {
  override fun configure(hc: OpenSshConfig.Host, session: Session) {
    if (hc.hostName.contains("gitlab.com")) {
      // TODO: Hack for host key checking for GitLab on laptop not doing what I expect
      // https://stackoverflow.com/questions/13396534/unknownhostkey-exception-in-accessing-github-securely
      session.setConfig("StrictHostKeyChecking", "no")
    }
  }
}

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
        .setTransportConfigCallback { transport ->
          if (transport is SshTransport) {
            transport.sshSessionFactory = sessionConfigFactory
          }
        }
        .call().use {
      LOGGER.info { "Cloned $directory to $remoteUrl" }
    }
  }
}

class ConfigureRemotesAction @Inject constructor(
    private val repository: File,
    private val remotes: Map<String, String>
) : Runnable {
  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  override fun run() {
    Git.open(repository).use { git ->
      val currentRemotes = git.remoteList().call()
          .onEach { require(it.urIs.size == 1) { "Only supports single URL from each remote" } }
          .associate { it.name to it.urIs.first().host }
      val toRemove = currentRemotes.filter { it.key !in remotes }
      val toAdd = remotes.filter { it.key !in currentRemotes }
      val toUpdate = remotes.filter { it.key in currentRemotes && currentRemotes[it.key] != it.value }

      toRemove.forEach { (name, _) ->
        LOGGER.debug { "Revmoiing remote named $name from repository ${git.repository.directory}" }
        git.remoteRemove().apply {
          setName(name)
        }.call()
      }
      toAdd.forEach { (name, uri) ->
        LOGGER.debug { "Add remote named $name with URI $uri to repository ${git.repository.directory}" }
        git.remoteAdd()
            .setName(name)
            .setUri(URIish(uri))
            .call()
      }
      toUpdate.forEach { (name, uri) ->
        LOGGER.debug { "Updating remote with name $name from URI ${currentRemotes[name]} to URI $uri in repository ${git.repository.directory}" }
        git.remoteSetUrl().apply {
          setName(name)
          setUri(URIish(uri))
        }.call()
      }
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
    Git.open(repository).use { git ->
      git.fetch()
          .setRemote(remote)
          .call()
      LOGGER.info { "Fetched remote $remote for ${git.repository.directory}" }
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
    Git.open(repository).use { git ->
      git.pull()
          .setRebase(true)
          .setRemote(remote)
          .setTransportConfigCallback { transport ->
            if (transport is SshTransport) {
              transport.sshSessionFactory = sessionConfigFactory
            }
          }
          .call()
      LOGGER.info { "Pulled $remote for ${git.repository.directory}" }
    }
  }
}

class StashAction @Inject constructor(
    private val repository: File
) : Runnable {
  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  override fun run() {
    Git.open(repository).use { git ->
      val stash = git.stashCreate()
          .setIndexMessage("Stashed from Gradle")
          .call()
      LOGGER.info { "Created stash ${stash.id} for ${git.repository.directory}" }
    }
  }
}

class UnstashAction @Inject constructor(
    private val repository: File
) : Runnable {
  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  override fun run() {
    Git.open(repository).use { git ->
      git.stashApply()
          .call()
      LOGGER.info { "Applied stash to ${git.repository.directory}" }
    }
  }
}
