package com.mkobit.chickendinner.chrome.internal.cdp

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import com.fasterxml.jackson.module.kotlin.treeToValue
import com.mkobit.chickendinner.chrome.RequestFrame
import com.mkobit.chickendinner.chrome.ResponseFrame
import io.ktor.http.cio.websocket.Frame
import io.ktor.http.cio.websocket.WebSocketSession
import io.ktor.http.cio.websocket.readBytes
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.broadcast
import kotlinx.coroutines.channels.consume
import kotlinx.coroutines.channels.filter
import kotlinx.coroutines.channels.first
import kotlinx.coroutines.channels.map
import kotlinx.coroutines.channels.mapNotNull
import kotlinx.coroutines.withContext
import java.util.concurrent.atomic.AtomicLong
import kotlin.reflect.full.functions

internal abstract class BaseKtorWebsocketDomain(
  private val session: WebSocketSession,
  private val objectMapper: ObjectMapper,
  private val requestIdGenerator: AtomicLong
) {

  protected suspend inline fun <reified T> sendAndAwait(requestParameters: Any? = null): T {
    val callingFrame = Thread.currentThread().stackTrace[1]
    // TODO: hacky

    val callingClass = Class.forName(callingFrame.className)
      .kotlin
    val callingFunction = callingClass.functions.first { it.name == callingFrame.methodName }

    val domain = callingFrame.className
      .substringBefore("Domain")
      .substringAfter("KtorClientWebsocket")
    val method = callingFrame.methodName
    val requestFrame = RequestFrame(requestIdGenerator.getAndIncrement(), "$domain.$method", requestParameters)
    val requestFrameText = objectMapper.writeValueAsString(requestFrame)
    val websocketFrame = Frame.Text(requestFrameText)
    session.send(websocketFrame)
    return session.incoming.broadcast()
      .consume {
        mapNotNull {
          withContext(Dispatchers.IO) {
            objectMapper.readValue<ResponseFrame>(it.readBytes())
          }
        }.filter { it.id == requestFrame.id }
          .map {
            withContext(Dispatchers.IO) {
              objectMapper.treeToValue<T>(it.result!!)
            }
          }
          .first()
      }
  }
}
