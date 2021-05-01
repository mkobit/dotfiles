package dotfiles.shell.ssh

import io.mkobit.ssh.config.HostConfig
import io.mkobit.ssh.config.SshConfig
import java.time.Duration
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.div

private const val CONTROL_PATH_FILE_NAME_PATTERN =
  "${SshConfig.REMOTE_USERNAME}@${SshConfig.REMOTE_HOSTNAME}:${SshConfig.REMOTE_PORT}"

@ExperimentalPathApi
internal fun commonAllHostsConfig(): List<HostConfig> = listOf(
  HostConfig(
    patterns = listOf("*"),
    sshConfig = SshConfig(
      controlMaster = SshConfig.ControlMaster.AUTO,
      controlPath = homeDir() / ".ssh" / "controlMaster" / CONTROL_PATH_FILE_NAME_PATTERN,
      controlPersist = Duration.ofMinutes(10),
      serverAliveCountMax = 18,
      serverAliveInterval = Duration.ofSeconds(10)
    )
  )
)
