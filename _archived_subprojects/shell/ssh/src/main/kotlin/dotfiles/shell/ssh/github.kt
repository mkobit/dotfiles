package dotfiles.shell.ssh

import io.mkobit.ssh.config.HostConfig
import io.mkobit.ssh.config.SshConfig
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.div

@ExperimentalPathApi
internal fun mkobitGithub(): List<HostConfig> = listOf(
  HostConfig(
    patterns = listOf("github.com"),
    sshConfig = SshConfig(
      identityFile = homeDir() / ".ssh" / "mkobit_github",
      identitiesOnly = true,
      user = "mkobit",
    )
  )
)
