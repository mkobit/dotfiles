@file:JvmName("Main")

package com.mkobit.dev

import ratpack.handling.Handler
import ratpack.server.RatpackServer
import java.net.InetAddress

object Main {

  @JvmStatic
  fun main(args: Array<String>) {
    RatpackServer.start { server ->
      server.serverConfig { serverConfigBuilder ->
        serverConfigBuilder.address(InetAddress.getLoopbackAddress())
        serverConfigBuilder.port(1337)
      }
      server.handlers { handlers ->
        handlers.get { context ->
          context.render("Hello world!")
        }
      }
    }
  }
}
