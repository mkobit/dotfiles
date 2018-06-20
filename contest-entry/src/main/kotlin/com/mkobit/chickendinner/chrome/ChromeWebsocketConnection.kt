package com.mkobit.chickendinner.chrome

import com.fasterxml.jackson.databind.ObjectMapper
import io.ktor.http.cio.websocket.WebSocketSession
import mu.KotlinLogging
import java.util.concurrent.atomic.AtomicLong

class ChromeWebsocketConnection(
    private val session: WebSocketSession,
    private val objectMapper: ObjectMapper
) {
  private val requestId = AtomicLong()

  companion object {
    private val logger = KotlinLogging.logger { }
  }

  suspend fun send(message: Any) {
//    val requestFrame = RequestFrame(requestId.incrementAndGet(), message)
//    session.outgoing.send(Frame.Text(objectMapper.writeValueAsString(requestFrameand fix )))
  }
}

