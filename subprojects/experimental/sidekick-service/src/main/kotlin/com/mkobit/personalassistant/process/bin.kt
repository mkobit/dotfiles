package com.mkobit.personalassistant.process

/**
 * pgrep - look up or signal processes based on name and other attributes
 * Follows same semantics as [pkill].
 */
suspend fun pgrep(
  full: Boolean = false,
  pattern: String? = null
): CompletedProcess {
  val arguments = mutableListOf("pgrep")
  if (full) {
    arguments.add("--full")
  }
  if (pattern != null) {
    arguments.add(pattern)
  }
  return runProcess(arguments)
}

/**
 * pkill - look up and signal processes based on name and other attributes
 *
 * Follows same semantics as [pgrep].
 */
suspend fun pkill(
  full: Boolean = false,
  pattern: String? = null
): CompletedProcess {
  val arguments = mutableListOf("pkill")
  if (full) {
    arguments.add("--full")
  }
  if (pattern != null) {
    arguments.add(pattern)
  }
  return runProcess(arguments)
}

/**
 * xargs - build and execute command lines from standard input
 */
suspend fun xargs(
  stdInput: String,
  noRunIfEmpty: Boolean = false,
  command: String
): CompletedProcess {
  val arguments = mutableListOf("xargs")
  if (noRunIfEmpty) {
    arguments.add("--no-run-if-empty")
  }
  arguments.add(command)

  return runProcess(arguments, stdIn = stdInput)
}

/**
 * ps - report a snapshot of the current processes.
 */
suspend fun ps(
  format: String? = null,
  noHeaders: Boolean = false
): CompletedProcess {
  val arguments = mutableListOf("ps")
  if (format != null) {
    arguments.add("-o")
    arguments.add(format)
  }
  if (noHeaders) {
    arguments.add("--no-headers")
  }
  return runProcess(arguments)
}
