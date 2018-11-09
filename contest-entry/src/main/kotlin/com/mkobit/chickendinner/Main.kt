package com.mkobit.chickendinner

import arrow.core.None
import arrow.core.Some
import arrow.core.orElse
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.registerKotlinModule
import com.mkobit.chickendinner.chrome.ChromeDebugger
import io.ktor.client.features.json.JsonFeature
import com.mkobit.chickendinner.chrome.determineChromePortFromLog
import com.mkobit.chickendinner.chrome.determineChromePortFromProfileFile
import com.mkobit.chickendinner.gmail.internal.CredentialsLocation
import com.mkobit.chickendinner.gmail.internal.WorkspaceDirectory
import io.ktor.client.HttpClient
import io.ktor.client.engine.HttpClientEngineFactory
import io.ktor.client.engine.cio.CIO
import io.ktor.client.features.json.JacksonSerializer
import io.ktor.client.features.websocket.WebSockets
import io.ktor.features.ContentNegotiation
import kotlinx.coroutines.runBlocking
import mu.KotlinLogging
import org.kodein.di.Kodein
import org.kodein.di.generic.bind
import org.kodein.di.generic.factory
import org.kodein.di.generic.instance
import org.kodein.di.generic.singleton
import java.nio.file.Path
import java.nio.file.Paths

object Main {

  private val ProjectDataRoot = Any()
  private val ChromeOutputLog = Any()
  private val ChromeUserData = Any()

  private val logger = KotlinLogging.logger { }

  private fun runtimePropertyFor(name: String) = System.getProperty("com.mkobit.chickendinner.$name")
//  private fun runtimePropertyFor(name: String) = System.getProperty("${Main::class.java.packageName}.$name")

  private fun newInjector(): Kodein = Kodein {
    bind<Path>(tag = CredentialsLocation) with singleton {
      Paths.get(runtimePropertyFor("gmailClientJsonPath"))
    }
    bind<Path>(tag = WorkspaceDirectory) with singleton {
      // Gmail workspace directory
      Paths.get(runtimePropertyFor("workspaceDirectory")).resolve("gmail")
    }
    bind<Path>(tag = ProjectDataRoot) with singleton { Paths.get("/tmp/.contestant") }
    bind<Path>(tag = ChromeOutputLog) with singleton { Paths.get("/tmp/startup_google-chrome.log") }
    bind<Path>(tag = ChromeUserData) with singleton { instance<Path>(tag = ProjectDataRoot).resolve("google-chrome-user-data") }
    bind<ObjectMapper>() with singleton { ObjectMapper().registerKotlinModule() }
    bind<HttpClientEngineFactory<*>>() with singleton { CIO }
    bind<HttpClient>() with singleton {
      HttpClient(engineFactory = instance<HttpClientEngineFactory<*>>()) {
        install(WebSockets)
        install(JsonFeature) {
          serializer = JacksonSerializer()
        }
      }
    }
    bind<ChromeDebugger>() with factory { debugPort: Int -> ChromeDebugger(debugPort, instance()) }
  }

  @JvmStatic
  fun main(args: Array<String>) {
    val injector = newInjector()
    val chromeLogs: Path by injector.instance(tag = ChromeOutputLog)
    val chromeDebugPort = determineChromePortFromLog(chromeLogs.toFile().readText())
        .orElse { determineChromePortFromProfileFile() }.let {
          when (it) {
            is Some -> it.t
            is None -> throw RuntimeException("Could not determine Chrome debug port")
          }
        }
    logger.info { "Chrome debug port determined to be running on $chromeDebugPort" }

    val chromeDebugger = run {
      val debuggerFactory: (Int) -> ChromeDebugger by injector.factory()
      debuggerFactory(chromeDebugPort)
    }

    runBlocking {
      chromeDebugger.version().let { logger.info { "Chrome version: $it" } }
      chromeDebugger.openedPages().forEach {
        println("${it.title} -> ${it.id}")
      }
//      val page = chromeDebugger.newPage()
//      delay(Duration.ofSeconds(5L))
//        chromeDebugger.withConnection(page) {
//          send(NavigateRequest("https://google.com"))
//        }
//      chromeDebugger.close(page)
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
