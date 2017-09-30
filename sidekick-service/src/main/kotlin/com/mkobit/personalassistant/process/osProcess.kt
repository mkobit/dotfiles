package com.mkobit.personalassistant.process

import kotlinx.coroutines.experimental.yield
import mu.KotlinLogging
import java.io.File

data class CompletedProcess(
    val arguments: List<String>,
    val returnCode: Int,
    val stdOut: String,
    val stdErr: String
)

private val logger = KotlinLogging.logger {}

suspend fun runProcess(
    commandLine: List<String>,
    environment: Map<String, String> = mapOf(),
    workingDir: File? = null,
    stdIn: String? = null
): CompletedProcess  {
  val processBuilder = ProcessBuilder().apply {
    command(commandLine)
    environment().putAll(environment)
    workingDir?.let { directory(it) }
  }

  val process = processBuilder.start()
  try {
    stdIn?.let {
      process.outputStream.bufferedWriter().also { writer ->
        writer.append(it)
        writer.flush()
      }
    }
    while (process.isAlive) {
      yield()
    }

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
