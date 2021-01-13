package io.mkobit.ssh.config

import java.nio.file.Path
import java.time.Duration

/**
 * - [SSH config manual](https://man7.org/linux/man-pages/man5/ssh_config.5.html)
 */
data class SshConfig(
  val includes: List<Path>? = null,
  val controlMaster: ControlMaster? = null,
  val controlPath: Path? = null,
  val controlPersist: Duration? = null,
  val identityFile: Path? = null,
  val identitiesOnly: Boolean? = null,
  val serverAliveCountMax: Int? = null,
  val serverAliveInterval: Duration? = null
) {

  init {
    controlPersist?.let {
      require(it > Duration.ZERO)
      require(it.toSeconds() > 0L)
    }
    serverAliveInterval?.let {
      require(it > Duration.ZERO)
      require(it.toSeconds() > 0L)
    }
  }

  companion object Token {

    /**
     * A literal ‘%’.
     */
    const val LITERAL_PERCENT = "%%"

    /**
     * Hash of `%l%h%p%r`.
     */
    const val DEFAULT = "%C"

    /**
     * Local user's home directory.
     */
    const val USER_HOME = "%d"

    /**
     * The remote hostname.
     */
    const val REMOTE_HOSTNAME = "%h"

    /**
     * The local user ID.
     */
    const val LOCAL_USER_ID = "%i"

    /**
     * The host key alias if specified, otherwise the orignal remote hostname given on the command line.
     */
    const val HOST_KEY_ALIAS = "%k"

    /**
     * The local hostname.
     */
    const val LOCAL_HOSTNAME = "%L"

    /**
     * The local hostname, including the domain name.
     */
    const val LOCAL_HOSTNAME_INCLUDING_DOMAIN = "%l"

    /**
     * The original remote hostname, as given on the command line.
     */
    const val ORIGINAL_REMOTE_HOSTNAME = "%n"

    /**
     * The remote port.
     */
    const val REMOTE_PORT = "%p"

    /**
     * The remote username.
     */
    const val REMOTE_USERNAME = "%r"

    /**
     * The local tun(4) or tap(4) network interface assigned if tunnel forwarding was requested, or "NONE" otherwise.
     */
    const val LOCAL_TUN = "%T"

    /**
     * The local username.
     */
    const val LOCAL_USERNAME = "%u"
  }

  enum class ControlMaster {
    AUTO
  }
}

// fun main() {
//  sshConfigFile(path) {
//    include(sshConfigFile)
//    host("") {
//
//    }
//  }
// }
