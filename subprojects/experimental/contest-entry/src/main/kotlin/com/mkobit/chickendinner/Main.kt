package com.mkobit.chickendinner

import arrow.core.None
import arrow.core.Some
import com.google.api.services.gmail.Gmail
import com.mkobit.cdp.domain.page.NavigateRequest
import com.mkobit.chickendinner.chrome.ChromeDebugger
import com.mkobit.chickendinner.chrome.determineChromePortFromProfileFile
import com.mkobit.chickendinner.chrome.internal.ChromeModule
import com.mkobit.chickendinner.gmail.EmailRetriever
import com.mkobit.chickendinner.gmail.internal.GmailModule
import com.typesafe.config.Config
import com.typesafe.config.ConfigFactory
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.time.delay
import mu.KotlinLogging
import org.kodein.di.Kodein
import org.kodein.di.generic.bind
import org.kodein.di.generic.factory
import org.kodein.di.generic.instance
import org.kodein.di.generic.provider
import org.kodein.di.generic.singleton
import java.lang.Exception
import java.nio.file.Path
import java.nio.file.Paths
import java.time.Duration

object Main {

  private object Tag {
    /**
     * Workspace root for all components.
     */
    object ProjectWorkspaceRoot

    /**
     * HOCON application configuration.
     */
    object ApplicationConfig
  }

  private val injector = Kodein {
    bind<Config>(tag = Tag.ApplicationConfig) with singleton {
      val configFile = Paths.get(runtimePropertyFor("appConfiguration"))
      ConfigFactory.parseFile(configFile.toFile())
    }
    bind<String>(tag = GmailModule.Tag.GmailUserId) with provider {
      instance<Config>(tag = Tag.ApplicationConfig).getString(applicationPropertyNameFor("gmail.userId"))
    }
    bind<Path>(tag = Tag.ProjectWorkspaceRoot) with singleton {
      Paths.get(runtimePropertyFor("workspaceDirectory"))
    }
    import(GmailModule.Module)
    bind<Path>(tag = GmailModule.Tag.CredentialsLocation) with singleton {
      Paths.get(runtimePropertyFor("gmailClientJsonPath"))
    }
    bind<Path>(tag = GmailModule.Tag.WorkspaceDirectory) with singleton {
      // GmailModule workspace directory
      instance<Path>(tag = Tag.ProjectWorkspaceRoot).resolve(".gmail")
    }
    import(ChromeModule.Module)
    bind<Path>(tag = ChromeModule.Tag.ChromeWorkspaceDirectory) with singleton {
      instance<Path>(tag = Tag.ProjectWorkspaceRoot).resolve(".chrome")
    }
  }

  private val logger = KotlinLogging.logger { }

  private fun applicationPropertyNameFor(name: String) = "com.mkobit.chickendinner.$name"
  private fun runtimePropertyFor(name: String) = System.getProperty(applicationPropertyNameFor(name))

  @JvmStatic
  fun main(args: Array<String>) {
//    ensureGmailLabelsPresent(injector)
    val retriever: EmailRetriever by injector.instance()
//    runBlocking {
//      launch(Dispatchers.Default) {
//        val emailMessages = retriever.retrieveEmails()
//        for (message in emailMessages) {
////          println(message)
//          if (message.payload?.parts == null) {
//            println("empty parts - ${message.snippet}")
//          }
//          message.payload?.parts?.let { parts ->
//            for (part in parts) {
////              println("${part.mimeType} - ${message.snippet}: ${part.body.decodeData().toString(UTF_8)}")
//              println("(parts = ${parts.size}) ${part.mimeType} - ${message.snippet}")
////              println(part.)
////              println("${message.snippet}")
//            }
//
//          }
//        }
//      }.join()
//    }

    runBlocking {
      val chromeLogs: Path by injector.instance()
//      val chromeDebugPort = determineChromePortFromLog(chromeLogs.toFile().readText())
//        .orElse { determineChromePortFromProfileFile() }.let {
//          when (it) {
//            is Some -> it.t
//            is None -> throw RuntimeException("Could not determine Chrome debug port")
//          }
//        }
      val chromeDebugPort = determineChromePortFromProfileFile().let {
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

      chromeDebugger.version().let { logger.info { "Chrome version: $it" } }
      chromeDebugger.openedPages().forEach {
        println("${it.title} -> ${it.id}")
      }
      val page = chromeDebugger.newPage()
      chromeDebugger.withConnection(page) {
//        pageDomain.navigate(NavigateRequest("https://google.com", null, null, null))
        try {
          val version = browserDomain.getVersion()
          logger.info { "Version: $version" }
        } catch (exception: Exception) {
          logger.error(exception) { "wtf" }
        }
      }
      delay(Duration.ofSeconds(5L))
      chromeDebugger.close(page)
//        logger.info { "Chrome Version: $version" }
//        version.webSocketDebuggerUrl
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
//    }
//      client.ws(host = "echo.websocket.org", path = "/") {
//        send(Frame.Text("Rock it with HTML5 WebSocket"))
//        incoming.receive().let {
//          when (it) {
//            is Frame.Text -> println(it.readText())
//          }
//        }
    }
  }

  private fun ensureGmailLabelsPresent(kodein: Kodein) {
    val gmail: Gmail by kodein.instance()
    val gmailUserId: String by kodein.instance(tag = GmailModule.Tag.GmailUserId)
    val currentLabels = gmail.users().labels().list(gmailUserId).execute().labels

    currentLabels.forEach {
      logger.info { "Gmail label: $it" }
    }
  }
}
