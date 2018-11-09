package com.mkobit.chickendinner.chrome

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import io.ktor.http.cio.websocket.Frame
import io.ktor.http.cio.websocket.WebSocketSession
import mu.KotlinLogging
import java.util.concurrent.atomic.AtomicLong

class ChromeWebsocketConnection(
    private val session: WebSocketSession,
    private val objectMapper: ObjectMapper
) {

  private val counter = AtomicLong()

  companion object {
    private val logger = KotlinLogging.logger { }
  }

  suspend fun send(method: String, params: Any?): ResponseFrame {
//    val requestFrame = RequestFrame(counter.incrementAndGet(), method, params)
//    session.outgoing.send(Frame.Text(objectMapper.writeValueAsString(requestFrame)))
//    for (frame in session.incoming) {
//      if (frame is Frame.Text) {
//        return objectMapper.readValue<ResponseFrame>(frame.buffer.array())
//      }
//    }
    TODO()
  }
}
