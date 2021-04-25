package io.mkobit.ssh.config

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import strikt.api.expectThat
import strikt.assertions.containsExactly
import java.nio.file.Path
import java.time.Duration
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.div

@ExperimentalPathApi
internal class SshConfigGeneratorTest {
  @Test
  internal fun `ssh config to text`(@TempDir directory: Path) {
    val config = SshConfig(
      includes = listOf(directory / "config1", directory / "config2"),
      controlPath = directory / "${SshConfig.REMOTE_USERNAME}@${SshConfig.REMOTE_HOSTNAME}:${SshConfig.REMOTE_PORT}",
      controlMaster = SshConfig.ControlMaster.AUTO,
      controlPersist = Duration.ofMinutes(10L),
      serverAliveCountMax = 18,
      serverAliveInterval = Duration.ofSeconds(15L),
      identityFile = directory / "identity_rsa"
    )
    println(config.asText())
    expectThat(config.asText().lines())
      .containsExactly(
        "Include \"${directory / "config1"}\"",
        "Include \"${directory / "config2"}\"",
        "ControlMaster auto",
        "ControlPath \"${directory / "%r@%h:%p"}\"",
        "ControlPersist 600s",
        "IdentityFile \"${directory / "identity_rsa"}\"",
        "ServerAliveCountMax 18",
        "ServerAliveInterval 15"
      )
  }

  @Test
  internal fun `host config to text`() {
    val config = HostConfig(
      listOf(
        "github.com",
        "google.com"
      ),
      SshConfig(
        identitiesOnly = true
      )
    )
    println(config.asText())
    expectThat(config.asText().lines())
      .containsExactly(
        "Host github.com google.com",
        "IdentitiesOnly yes".prependIndent(" ".repeat(4))
      )
  }
}
