package com.mkobit.chickendinner

import arrow.core.None
import arrow.core.Some
import arrow.core.orElse
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.registerKotlinModule
import com.mkobit.chickendinner.chrome.determineChromePortFromLog
import com.mkobit.chickendinner.chrome.determineChromePortFromProfileFile
import com.mkobit.chickendinner.json.JacksonSerializer
import io.ktor.client.HttpClient
import io.ktor.client.engine.HttpClientEngineFactory
import io.ktor.client.engine.cio.CIO
import io.ktor.client.features.json.JsonFeature
import io.ktor.client.features.websocket.WebSockets
import io.ktor.client.features.websocket.webSocketRawSession
import io.ktor.client.features.websocket.ws
import io.ktor.http.HttpMethod
import io.ktor.http.cio.websocket.Frame
import io.ktor.http.cio.websocket.readText
import kotlinx.coroutines.experimental.channels.filterNotNull
import kotlinx.coroutines.experimental.channels.map
import kotlinx.coroutines.experimental.runBlocking
import kotlinx.coroutines.experimental.time.delay
import mu.KotlinLogging
import org.kodein.di.Kodein
import org.kodein.di.generic.bind
import org.kodein.di.generic.instance
import org.kodein.di.generic.singleton
import java.nio.file.Path
import java.nio.file.Paths
import java.time.Duration

object Main {

  private val ProjectDataRoot = Any()
  private val ChromeOutputLog = Any()
  private val ChromeUserData = Any()

  private val logger = KotlinLogging.logger { }

  private fun newInjector(): Kodein = Kodein {
    bind<Path>(tag = ProjectDataRoot) with singleton { Paths.get("/tmp/.contestant") }
    bind<Path>(tag = ChromeOutputLog) with singleton { Paths.get("/tmp/startup_google-chrome.log") }
    bind<Path>(tag = ChromeUserData) with singleton { instance<Path>(tag = ProjectDataRoot).resolve("google-chrome-user-data") }
    bind<ObjectMapper>() with singleton { ObjectMapper().registerKotlinModule() }
    bind<HttpClientEngineFactory<*>>() with singleton { CIO }
    bind<HttpClient>() with singleton {
      HttpClient(instance()) {
        install(WebSockets)
        install(JsonFeature) {
          serializer = JacksonSerializer(instance())
        }
      }
    }
  }

  @JvmStatic fun main(args: Array<String>) {
    val injector = newInjector()
    val client: HttpClient by injector.instance()
    val chromeLogs: Path by injector.instance(tag = ChromeOutputLog)
    val chromeDebugPort = determineChromePortFromLog(chromeLogs.toFile().readText())
        .orElse { determineChromePortFromProfileFile() }.let {
      when (it) {
        is None -> throw RuntimeException("Could not determine Chrome debug port")
        is Some -> it.t
      }
    }
    logger.info { "Chrome debug port determined to be running on $chromeDebugPort" }

    runBlocking {
//      val browserDebugUrl = retrieveVersion(client, chromeDebugPort).let { version ->
//        logger.info { "Chrome Version: $version" }
//        version.webSocketDebuggerUrl
//      }
//      val path = retrievePages(client, chromeDebugPort).let { pages ->
////        logger.debug { "Current open pages: $pages" }
//        pages.first().webSocketDebuggerUrl.run {
//          subSequence(indexOf("/devtools"), length)
//        }
//      }
//      logger.info { "Connecting to page at path $path" }
//      client.ws(method = HttpMethod.Get, host = "localhost", port = chromeDebugPort, path = path.toString()) {
//        send(Frame.Text("""{"id": 1, "method": "Browser.getVersion" }"""))
//        println("hey")
//
//        println(incoming.isClosedForReceive)
//        println()
//        println("receive: ${incoming.receive()}")
//        for (message in incoming) {
//          println(message::class)
//        }
//        for (message in incoming.map { it as? Frame.Text }.filterNotNull()) {
//          logger.info { "Frame text from WS: ${message.readText()}" }
//        }
      }
//      client.ws(host = "echo.websocket.org", path = "/") {
//        send(Frame.Text("Rock it with HTML5 WebSocket"))
//        incoming.receive().let {
//          when (it) {
//            is Frame.Text -> println(it.readText())
//          }
//        }
////        for (message in incoming) {
////          println(message)
////        }
//      }
//    }
  }
}
