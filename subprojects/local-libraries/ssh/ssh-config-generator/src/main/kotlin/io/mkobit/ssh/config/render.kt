package io.mkobit.ssh.config

fun SshConfig.asText(): String = (
  (includes?.map { "Include \"$it\"" } ?: emptyList()) +
    listOfNotNull(
      controlMaster?.let { "ControlMaster ${it.name.toLowerCase()}" },
      controlPath?.let { "ControlPath \"$it\"" },
      controlPersist?.let { "ControlPersist ${it.toSeconds()}s" },
      identityFile?.let { "IdentityFile \"$it\"" },
      identitiesOnly?.let { "IdentitiesOnly ${if (it) "yes" else "no"}" },
      serverAliveCountMax?.let { "ServerAliveCountMax $it" },
      serverAliveInterval?.let { "ServerAliveInterval ${it.toSeconds()}" },
    )
).joinToString(separator = System.lineSeparator())

fun HostConfig.asText(): String =
  "Host ${patterns.joinToString(separator = " ")}" +
    System.lineSeparator() +
    sshConfig.asText().prependIndent(indent = " ".repeat(4))

fun List<HostConfig>.asText(): String =
  joinToString(separator = System.lineSeparator().repeat(2)) { it.asText() }
