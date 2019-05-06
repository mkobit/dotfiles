@file:JvmName("Main")

package com.mkobit.personalassistant

import io.ktor.application.call
import io.ktor.application.install
import io.ktor.http.ContentType
import io.ktor.response.respondText
import io.ktor.routing.Routing
import io.ktor.routing.get
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty

fun main(args: Array<String>) {
  val server = embeddedServer(Netty, 8080) {
    install(Routing) {
      get("/") {
        call.respondText("Hello, world!", ContentType.Text.Html)
      }
    }
  }
  server.start(wait = true)
}
