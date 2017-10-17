@file:JvmName("Main")

package com.mkobit.personalassistant

import com.mkobit.personalassistant.chrome.chromeRouter
import io.vertx.core.AbstractVerticle
import io.vertx.core.Future
import io.vertx.core.Handler
import io.vertx.ext.web.Router
import io.vertx.ext.web.RoutingContext
import io.vertx.kotlin.core.http.HttpServerOptions

@Suppress("UNUSED")
class Main : AbstractVerticle() {
//  @JvmStatic
//  fun main(args: Array<String>) {
//
//  }

  override fun start(startFuture: Future<Void>) {
    val router = createRouter()
    vertx.createHttpServer(serverOptions).requestHandler(router::accept).listen { result ->
      when {
        result.succeeded() -> startFuture.complete()
        else -> startFuture.fail(result.cause())
      }
    }
  }

  val serverOptions = HttpServerOptions(
      port = 1337
  )

  fun createRouter(): Router = Router.router(vertx).apply {
    get("/").handler(handlerRoot)
    mountSubRouter("/browser/chrome", chromeRouter(vertx))
  }

  val handlerRoot = Handler<RoutingContext> { req ->
    req.response().end("Hello World!")
  }
}
