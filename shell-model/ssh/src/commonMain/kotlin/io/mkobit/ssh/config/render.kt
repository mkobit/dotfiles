package io.mkobit.ssh.config

private fun Boolean.asYesNo(): String = if (this) "yes" else "no"

fun SshConfig.asText(): String = buildList {
  includes?.forEach { add("""Include "$it"""") }
  addKeysToAgent?.let { add("AddKeysToAgent ${it.asYesNo()}") }
  controlMaster?.let { add("ControlMaster ${it.name.lowercase()}") }
  controlPath?.let { add("""ControlPath "$it"""") }
  controlPersist?.let { add("ControlPersist ${it.inWholeSeconds}s") }
  identityFile?.let { add("""IdentityFile "$it"""") }
  identitiesOnly?.let { add("IdentitiesOnly ${it.asYesNo()}") }
  serverAliveCountMax?.let { add("ServerAliveCountMax $it") }
  serverAliveInterval?.let { add("ServerAliveInterval ${it.inWholeSeconds}") }
  user?.let { add("User $it") }
}.joinToString(separator = "\n")


fun HostConfig.asText(): String = buildString {
  append("Host")
  patterns.forEach {
    append(' ')
    append(it)
  }
  appendLine()
  sshConfig.asText().let {
    if (it.isNotBlank()) append(it.prependIndent(" ".repeat(4)))
  }
}

fun Collection<HostConfig>.asText(): String =
  joinToString(separator = "\n".repeat(2)) { it.asText() }
