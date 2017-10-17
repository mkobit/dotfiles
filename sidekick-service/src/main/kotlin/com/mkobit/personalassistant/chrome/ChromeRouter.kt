package com.mkobit.personalassistant.chrome

import com.github.salomonbrys.kodein.Kodein
import com.github.salomonbrys.kodein.bind
import com.github.salomonbrys.kodein.instance
import com.github.salomonbrys.kodein.singleton
import com.github.salomonbrys.kodein.with
import io.vertx.core.Vertx
import io.vertx.ext.web.Router
import kotlinx.coroutines.experimental.launch
import kotlinx.coroutines.experimental.newFixedThreadPoolContext
import kotlin.coroutines.experimental.CoroutineContext

fun chromeRouter(vertx: Vertx): Router = Router.router(vertx).apply {
  val kodein = Kodein {
    constant("ChromeDebugPort") with 1337
    bind<CoroutineContext>() with singleton { newFixedThreadPoolContext(10, "ProcessLauncher") }
    bind<ChromeController>() with singleton { BackgroundProcessChromeController(instance("ChromeDebugPort"), instance()) }
  }
  route().handler { ctx ->
    val chromeController: ChromeController = kodein.instance()
    val context: CoroutineContext = kodein.instance()

    launch(context) {
      chromeController.start().join()
    }
    ctx.next()
  }
  post("/tabs/open").handler { ctx ->
    ctx.response().setStatusCode(200).end("Hey")
  }
  get("/tabs").handler { ctx ->
    ctx.response().end("Tabs!")
  }
}
