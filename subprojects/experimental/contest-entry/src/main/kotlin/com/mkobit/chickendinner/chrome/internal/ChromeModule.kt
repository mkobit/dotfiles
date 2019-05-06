package com.mkobit.chickendinner.chrome.internal

import arrow.core.None
import arrow.core.Some
import arrow.core.orElse
import com.mkobit.chickendinner.chrome.ChromeDebugger
import com.mkobit.chickendinner.chrome.determineChromePortFromLog
import com.mkobit.chickendinner.chrome.determineChromePortFromProfileFile
import io.ktor.client.HttpClient
import io.ktor.client.engine.HttpClientEngineFactory
import io.ktor.client.engine.cio.CIO
import io.ktor.client.features.json.JacksonSerializer
import io.ktor.client.features.json.JsonFeature
import io.ktor.client.features.websocket.WebSockets
import mu.KotlinLogging
import org.kodein.di.Kodein
import org.kodein.di.generic.bind
import org.kodein.di.generic.factory
import org.kodein.di.generic.instance
import org.kodein.di.generic.singleton
import java.nio.file.Path
import java.nio.file.Paths

object ChromeModule {

  private val LOGGER = KotlinLogging.logger { }

  object Tag {
    /**
     * Tag for working directory to store files.
     */
    object ChromeWorkspaceDirectory
  }

  val Module = Kodein.Module(name = ChromeModule::class.qualifiedName!!) {
    bind<ChromeDebugger>() with singleton {
      // TODO: this should be better integrated
      val chromeLogs: Path = Paths.get("/tmp/startup_google-chrome.log")
      val chromeDebugPort = determineChromePortFromLog(chromeLogs.toFile().readText())
          .orElse { determineChromePortFromProfileFile() }.let {
            when (it) {
              is Some -> it.t
              is None -> throw RuntimeException("Could not determine Chrome debug port")
            }
          }
      LOGGER.info { "Chrome debug port determined to be running on $chromeDebugPort" }

      ChromeDebugger(chromeDebugPort, instance())
    }
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
}
