package io.mkobit.ssh.config

private fun <T> T?.toLine(block: (T) -> String): String =
  this?.let { "${block(it)}${System.lineSeparator()}" } ?: ""

fun SshConfig.asText(): String =
  (
    (includes?.joinToString(separator = System.lineSeparator(), postfix = System.lineSeparator()) { "Include \"$it\"" } ?: "") +
      controlMaster.toLine { "ControlMaster ${it.name.toLowerCase()}" } +
      controlPath.toLine { "ControlPath \"$it\"" } +
      controlPersist.toLine { "ControlPersist ${it.toSeconds()}s" } +
      identityFile.toLine { "IdentityFile \"$it\"" } +
      identitiesOnly.toLine { "IdentitiesOnly ${if (it) "yes" else "no"}" } +
      serverAliveCountMax.toLine { "ServerAliveCountMax $it" } +
      serverAliveInterval.toLine { "ServerAliveInterval ${it.toSeconds()}" }
    ).trimEnd()

fun HostConfig.asText(): String =
  "Host ${patterns.joinToString(separator = " ")}" +
    System.lineSeparator() +
    sshConfig.asText().prependIndent(indent = " ".repeat(4))
