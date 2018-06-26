package com.mkobit.chickendinner.chrome

import com.fasterxml.jackson.module.kotlin.readValue
import com.mkobit.chickendinner.json.JacksonSerializer
import io.ktor.client.HttpClient
import io.ktor.client.features.feature
import io.ktor.client.features.json.JsonFeature
import io.ktor.client.features.websocket.ws
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.http.cio.websocket.Frame
import io.ktor.http.encodeURLPart
import kotlinx.coroutines.experimental.channels.map

class ChromeDebugger(
    private val debugPort: Int,
    private val client: HttpClient,
    private val host: String = "localhost"
) {
  suspend fun newPage(url: String? = null): PageInfo = client.post {
    url {
      host = this@ChromeDebugger.host
      port = debugPort
      path("json", "new")
      if (url != null) {
        parameters["url"] = url
      }
    }
  }

  suspend fun openedPages(): List<PageInfo> = client.get {
    url {
      host = this@ChromeDebugger.host
      port = debugPort
      path("json")
    }
  }

  // For valid targets, response body is "Target activated"
  suspend fun activate(pageId: String): String = client.post {
    url {
      host = this@ChromeDebugger.host
      port = debugPort
      path("json", "activate", pageId)
    }
  }

  suspend fun activate(pageInfo: PageInfo) = activate(pageInfo.id)

  // For valid targets, response body is "Target is closing"
  suspend fun close(pageId: String): String = client.post {
    url {
      host = this@ChromeDebugger.host
      port = debugPort
      path("json", "close", pageId)
    }
  }

  suspend fun close(pageInfo: PageInfo) = close(pageInfo.id)

  suspend fun version(): ProtocolVersion = client.get {
    url {
      host = this@ChromeDebugger.host
      port = debugPort
      path("json", "version")
    }
  }

  suspend fun withConnection(pageInfo: PageInfo, block: suspend ChromeWebsocketConnection.() -> Unit) =
      withConnection(pageInfo.id, block)

  suspend fun withConnection(pageId: String, block: suspend ChromeWebsocketConnection.() -> Unit) {
    client.ws(
        host = this@ChromeDebugger.host,
        port = debugPort,
        path = listOf("devtools", "page", pageId).joinToString("/", prefix = "/") { encodeURLPart(it) }
    ) {
      //      ChromeWebsocketConnection()
//      send(Frame.Text())
    }
  }
}
