package com.mkobit.chickendinner.chrome

import com.fasterxml.jackson.module.kotlin.readValue
import com.mkobit.chickendinner.json.JacksonSerializer
import io.ktor.client.HttpClient
import io.ktor.client.features.feature
import io.ktor.client.features.json.JsonFeature
import io.ktor.client.features.websocket.ws
import io.ktor.client.request.get
import io.ktor.client.request.post
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
      if (url != null) {
        parameters["url"] = url
      }
    }
  }

  suspend fun openedPages(): List<PageInfo> {
    // Can't use get<List<ChromePage>> right now https://github.com/ktorio/ktor/issues/346
    val responseData = client.get<ByteArray> {
      url {
        host = this@ChromeDebugger.host
        port = debugPort
        path("json")
      }
    }
    return (client.feature(JsonFeature)!!.serializer as JacksonSerializer).objectMapper.readValue(responseData)
  }

  // For valid targets, response body is "Target activated"
  suspend fun activate(pageId: String): String = client.post {
    url {
      host = this@ChromeDebugger.host
      port = debugPort
      path("json", "activate", pageId)
    }
  }

  // For valid targets, response body is "Target is closing"
  suspend fun close(pageId: String): String = client.post {
    url {
      host = this@ChromeDebugger.host
      port = debugPort
      path("json", "close", pageId)
    }
  }

  suspend fun version(): ProtocolVersion = client.get {
    url {
      host = this@ChromeDebugger.host
      port = debugPort
      path("json", "version")
    }
  }

  suspend fun withConnection(pageInfo: PageInfo, block: suspend ChromeWebsocketConnection.() -> Unit) {
    client.ws(
        host = this@ChromeDebugger.host,
        port = debugPort,
        path = pageInfo.debugUrlPath
    ) {
//      ChromeWebsocketConnection()
    }
  }

  private val PageInfo.debugUrlPath: String get() = webSocketDebuggerUrl.run {
    substring(indexOf("/devtools"), length)
  }
}
