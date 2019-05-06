package com.mkobit.personalassistant.process

import kotlinx.coroutines.future.await
import mu.KotlinLogging
import java.io.File

data class CompletedProcess(
  val arguments: List<String>,
  val returnCode: Int,
  val stdOut: String,
  val stdErr: String
) {
  fun throwIfNonZero(): CompletedProcess {
    if (returnCode != 0) {
      throw RuntimeException("Process $arguments exited with $returnCode\nStdErr: $stdErr")
    }
    return this
  }
}

private val logger = KotlinLogging.logger {}

suspend fun runProcess(
  commandLine: List<String>,
  environment: Map<String, String> = mapOf(),
  workingDir: File? = null,
  stdIn: String? = null
): CompletedProcess {
  val processBuilder = ProcessBuilder().apply {
    command(commandLine)
    environment().putAll(environment)
    workingDir?.let { directory(it) }
  }

  logger.debug { "Executing process with command $commandLine" }
  val process = processBuilder.start()
  try {
    stdIn?.let {
      process.outputStream.bufferedWriter().also { writer ->
        writer.append(it)
        writer.flush()
      }
    }
    process.onExit().await()

    val exitCode = process.exitValue()
    val stdOutText = process.inputStream.bufferedReader().use { it.readText() }
    val errorText = process.errorStream.bufferedReader().use { it.readText() }

    return CompletedProcess(commandLine, exitCode, stdOutText, errorText)
  } finally {
    if (process.isAlive) {
      logger.warn { "Process with arguments $commandLine did not finish successfully so terminating" }
      process.destroy()
    }
  }
}
