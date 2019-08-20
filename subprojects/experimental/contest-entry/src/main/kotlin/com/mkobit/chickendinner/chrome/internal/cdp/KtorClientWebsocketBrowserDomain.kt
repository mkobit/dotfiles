package com.mkobit.chickendinner.chrome.internal.cdp

import com.fasterxml.jackson.databind.ObjectMapper
import com.mkobit.cdp.domain.browser.BrowserDomain
import com.mkobit.cdp.domain.browser.GetBrowserCommandLineReply
import com.mkobit.cdp.domain.browser.GetHistogramReply
import com.mkobit.cdp.domain.browser.GetHistogramRequest
import com.mkobit.cdp.domain.browser.GetHistogramsReply
import com.mkobit.cdp.domain.browser.GetHistogramsRequest
import com.mkobit.cdp.domain.browser.GetVersionReply
import com.mkobit.cdp.domain.browser.GetWindowBoundsReply
import com.mkobit.cdp.domain.browser.GetWindowBoundsRequest
import com.mkobit.cdp.domain.browser.GetWindowForTargetReply
import com.mkobit.cdp.domain.browser.GetWindowForTargetRequest
import com.mkobit.cdp.domain.browser.GrantPermissionsRequest
import com.mkobit.cdp.domain.browser.ResetPermissionsRequest
import com.mkobit.cdp.domain.browser.SetWindowBoundsRequest
import io.ktor.http.cio.websocket.WebSocketSession
import java.util.concurrent.atomic.AtomicLong

internal class KtorClientWebsocketBrowserDomain(
  session: WebSocketSession,
  objectMapper: ObjectMapper,
  requestIdGenerator: AtomicLong
) : BaseKtorWebsocketDomain(session, objectMapper, requestIdGenerator), BrowserDomain {
  override suspend fun grantPermissions(request: GrantPermissionsRequest) = sendAndAwait<Unit>(request)

  override suspend fun resetPermissions(request: ResetPermissionsRequest) = sendAndAwait<Unit>(request)

  override suspend fun close() = sendAndAwait<Unit>()

  override suspend fun crash() = sendAndAwait<Unit>()

  override suspend fun getVersion(): GetVersionReply = sendAndAwait()

  override suspend fun getBrowserCommandLine(): GetBrowserCommandLineReply = sendAndAwait()

  override suspend fun getHistograms(request: GetHistogramsRequest): GetHistogramsReply = sendAndAwait(request)

  override suspend fun getHistogram(request: GetHistogramRequest): GetHistogramReply = sendAndAwait(request)

  override suspend fun getWindowBounds(request: GetWindowBoundsRequest): GetWindowBoundsReply = sendAndAwait(request)

  override suspend fun getWindowForTarget(request: GetWindowForTargetRequest): GetWindowForTargetReply = sendAndAwait(request)

  override suspend fun setWindowBounds(request: SetWindowBoundsRequest) = sendAndAwait<Unit>(request)
}
