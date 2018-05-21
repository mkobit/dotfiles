package com.mkobit.chickendinner.chrome

import kotlinx.coroutines.experimental.channels.ReceiveChannel
import kotlinx.coroutines.experimental.channels.SendChannel
import mu.KotlinLogging
import java.util.concurrent.atomic.AtomicInteger

class ChromeWebsocketConnection(
    val incoming: ReceiveChannel<Any>,
    val outgoing: SendChannel<Any>
) {
  private val requestId = AtomicInteger()

  companion object {
    private val logger = KotlinLogging.logger { }
  }

  suspend fun send(message: Any) {

  }
}

