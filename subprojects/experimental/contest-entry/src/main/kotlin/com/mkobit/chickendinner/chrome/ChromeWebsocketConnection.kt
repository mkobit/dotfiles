package com.mkobit.chickendinner.chrome

import com.fasterxml.jackson.databind.ObjectMapper
import com.mkobit.cdp.domain.browser.BrowserDomain
import com.mkobit.cdp.domain.page.PageDomain
import com.mkobit.chickendinner.chrome.internal.cdp.KtorClientWebsocketBrowserDomain
import com.mkobit.chickendinner.chrome.internal.cdp.KtorClientWebsocketPageDomain
import io.ktor.http.cio.websocket.WebSocketSession
import mu.KotlinLogging
import java.util.concurrent.atomic.AtomicLong

class ChromeWebsocketConnection(
  private val session: WebSocketSession,
  private val objectMapper: ObjectMapper
) {

  private val counter = AtomicLong()

  companion object {
    private val logger = KotlinLogging.logger { }
  }

  val pageDomain: PageDomain
    get() = KtorClientWebsocketPageDomain(session, objectMapper, counter)

  val browserDomain: BrowserDomain
    get() = KtorClientWebsocketBrowserDomain(session, objectMapper, counter)
}
