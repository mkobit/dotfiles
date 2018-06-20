package com.mkobit.chickendinner.chrome

import arrow.core.None
import arrow.core.Option
import arrow.core.Some
import arrow.core.Try
import com.google.common.io.Files
import java.nio.file.Path
import java.nio.file.Paths

fun launchChrome(
    userDataDirectory: Path,
    executable: Path = Paths.get("/usr/bin/google-chrome"),
    debugPort: Int = 0
): Process = ProcessBuilder().apply {
  command(
      executable.toAbsolutePath().toString(),
      "--userDataDirectory=${userDataDirectory.toAbsolutePath()}",
      "--new-window",
      "--remote-debugging-port=$debugPort"
  )
}.start()

private val CHROME_PORT_LOG_REGEX = Regex("^DevTools listening on [\\w]+://\\d+\\.\\d\\.\\d\\.\\d:(\\d+).*$")
fun determineChromePortFromLog(errorLog: String): Option<Int> {
  val line = errorLog.lineSequence().firstOrNull { it.contains("DevTools listening on") }
  return if (line == null) {
    None
  } else {
    val matchResult = CHROME_PORT_LOG_REGEX.matchEntire(line)
    if (matchResult == null) {
      None
    } else {
      Some(matchResult.groupValues[1].toInt())
    }
  }
}

fun determineChromePortFromProfileFile(
    profile: Path = Paths.get(
        System.getProperty("user.home")!!,
        ".config",
        ".config",
        "google-chrome",
        "DevToolsActivePort"
    )
): Option<Int> {
  return Try { Files.readLines(profile.toFile(), Charsets.UTF_8) }
      .map { it.first() }
      .map { it.toInt() }
      .toOption()
}
