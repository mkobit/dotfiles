package io.mkobit.ssh.config

import io.kotest.core.spec.style.FunSpec
import io.kotest.matchers.collections.shouldContainExactly
import okio.Path.Companion.toPath
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

internal class SshConfigGeneratorTest : FunSpec({
  val directory = "/tmp/test".toPath()

  test("ssh config to text") {
    val config = SshConfig(
      includes = listOf(directory / "config1", directory / "config2"),
      controlPath = directory / buildString {
        append(SshConfig.REMOTE_USERNAME)
        append("@")
        append(SshConfig.REMOTE_HOSTNAME)
        append(":")
        append(SshConfig.REMOTE_PORT)
      },
      controlMaster = SshConfig.ControlMaster.AUTO,
      controlPersist = 10.minutes,
      serverAliveCountMax = 18,
      serverAliveInterval = 15.seconds,
      identityFile = directory / "identity_rsa"
    )
    config.asText().lines()
      .shouldContainExactly(
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

  test("host config to text") {
    val config = HostConfig(
      listOf(
        "github.com",
        "google.com"
      ),
      SshConfig(
        identitiesOnly = true
      )
    )
    config.asText().lines()
      .shouldContainExactly(
        "Host github.com google.com",
        "IdentitiesOnly yes".prepend4Spaces()
      )
  }

  test("list of host configs to text") {
    val configs = listOf(
      HostConfig(listOf("host1"), SshConfig(identitiesOnly = true)),
      HostConfig(listOf("host2"), SshConfig(identitiesOnly = false)),
    )
    configs.asText().lines()
      .shouldContainExactly(
        "Host host1",
        "IdentitiesOnly yes".prepend4Spaces(),
        "",
        "Host host2",
        "IdentitiesOnly no".prepend4Spaces()
      )
  }
})

private fun String.prepend4Spaces(): String = prependIndent(" ".repeat(4))
