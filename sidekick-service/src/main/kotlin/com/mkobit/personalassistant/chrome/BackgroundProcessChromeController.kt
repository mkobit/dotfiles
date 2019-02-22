package com.mkobit.personalassistant.chrome

import com.mkobit.personalassistant.process.pgrep
import com.mkobit.personalassistant.process.runProcess
import com.mkobit.personalassistant.process.xargs
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import mu.KotlinLogging
import kotlin.coroutines.CoroutineContext

class BackgroundProcessChromeController constructor(
    private val debugPort: Int,
    private val processLauncherContext: CoroutineContext
) : ChromeController {

  init {
    require(debugPort in 1000..65535)
  }

  companion object {
    private val logger = KotlinLogging.logger {}
  }

  override suspend fun start(): Job {
    return GlobalScope.launch(processLauncherContext) {
      val chromeRunning = pgrep(pattern = "chrome")
      if (chromeRunning.returnCode != 0) {
        logger.debug { "No chrome process appears to be running, starting a new one on $debugPort" }
        runProcess(listOf("google-chrome", "--remote-debugging-port=$debugPort")).throwIfNonZero()
      } else {
        val psDetails = xargs(chromeRunning.stdOut, true, "ps").throwIfNonZero()
        if (!psDetails.stdOut.contains("--remote-debugging-port")) {
          logger.info { "Chrome not detected to be running in debug mode, starting process" }
          runProcess(listOf("google-chrome", "--remote-debugging-port=$debugPort")).throwIfNonZero()
        } else {
          logger.debug { "Chrome already running with debug port" }
        }
      }
    }
  }
}
