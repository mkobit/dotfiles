package io.mkobit.ssh.config

data class HostConfig(
  val patterns: List<String>,
  val sshConfig: SshConfig
) {
  init {
    require(patterns.isNotEmpty())
    require(patterns.all { it.isNotBlank() })
  }
}
