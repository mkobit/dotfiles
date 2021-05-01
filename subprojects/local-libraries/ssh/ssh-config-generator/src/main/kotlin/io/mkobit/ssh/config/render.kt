package io.mkobit.ssh.config

fun SshConfig.asText(): String = (
  (includes?.map { "Include \"$it\"" } ?: emptyList()) +
    listOfNotNull(
      addKeysToAgent?.let { "AddKeysToAgent ${it.asYesNo()}" },
      controlMaster?.let { "ControlMaster ${it.name.toLowerCase()}" },
      controlPath?.let { "ControlPath \"$it\"" },
      controlPersist?.let { "ControlPersist ${it.toSeconds()}s" },
      identityFile?.let { "IdentityFile \"$it\"" },
      identitiesOnly?.let { "IdentitiesOnly ${it.asYesNo()}" },
      serverAliveCountMax?.let { "ServerAliveCountMax $it" },
      serverAliveInterval?.let { "ServerAliveInterval ${it.toSeconds()}" },
      user?.let { "User $it" },
    )
).joinToString(separator = System.lineSeparator())

private fun Boolean.asYesNo(): String = if (this) "yes" else "no"

fun HostConfig.asText(): String =
  "Host ${patterns.joinToString(separator = " ")}" +
    System.lineSeparator() +
    sshConfig.asText().prependIndent(indent = " ".repeat(4))

fun List<HostConfig>.asText(): String =
  joinToString(separator = System.lineSeparator().repeat(2)) { it.asText() }
