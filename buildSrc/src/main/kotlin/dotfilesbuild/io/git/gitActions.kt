package dotfilesbuild.io.git

import com.jcraft.jsch.Session
import mu.KotlinLogging
import org.eclipse.jgit.api.Git
import org.eclipse.jgit.transport.JschConfigSessionFactory
import org.eclipse.jgit.transport.OpenSshConfig
import org.eclipse.jgit.transport.SshTransport
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
          .setTransportConfigCallback { transport ->
            if (transport is SshTransport) {
              transport.sshSessionFactory = sessionConfigFactory
            }
          }
          .call()
      LOGGER.info { "Pulled origin for $repository" }
    }
  }
}
