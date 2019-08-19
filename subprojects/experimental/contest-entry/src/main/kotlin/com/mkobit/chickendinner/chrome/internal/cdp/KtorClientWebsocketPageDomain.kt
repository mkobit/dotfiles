package com.mkobit.chickendinner.chrome.internal.cdp

import com.fasterxml.jackson.databind.ObjectMapper
import com.mkobit.cdp.domain.page.AddCompilationCacheRequest
import com.mkobit.cdp.domain.page.AddScriptToEvaluateOnLoadReply
import com.mkobit.cdp.domain.page.AddScriptToEvaluateOnLoadRequest
import com.mkobit.cdp.domain.page.AddScriptToEvaluateOnNewDocumentReply
import com.mkobit.cdp.domain.page.AddScriptToEvaluateOnNewDocumentRequest
import com.mkobit.cdp.domain.page.CaptureScreenshotReply
import com.mkobit.cdp.domain.page.CaptureScreenshotRequest
import com.mkobit.cdp.domain.page.CaptureSnapshotReply
import com.mkobit.cdp.domain.page.CaptureSnapshotRequest
import com.mkobit.cdp.domain.page.CreateIsolatedWorldReply
import com.mkobit.cdp.domain.page.CreateIsolatedWorldRequest
import com.mkobit.cdp.domain.page.DeleteCookieRequest
import com.mkobit.cdp.domain.page.GenerateTestReportRequest
import com.mkobit.cdp.domain.page.GetAppManifestReply
import com.mkobit.cdp.domain.page.GetCookiesReply
import com.mkobit.cdp.domain.page.GetFrameTreeReply
import com.mkobit.cdp.domain.page.GetLayoutMetricsReply
import com.mkobit.cdp.domain.page.GetNavigationHistoryReply
import com.mkobit.cdp.domain.page.GetResourceContentReply
import com.mkobit.cdp.domain.page.GetResourceContentRequest
import com.mkobit.cdp.domain.page.GetResourceTreeReply
import com.mkobit.cdp.domain.page.HandleJavaScriptDialogRequest
import com.mkobit.cdp.domain.page.NavigateReply
import com.mkobit.cdp.domain.page.NavigateRequest
import com.mkobit.cdp.domain.page.NavigateToHistoryEntryRequest
import com.mkobit.cdp.domain.page.PageDomain
import com.mkobit.cdp.domain.page.PrintToPDFReply
import com.mkobit.cdp.domain.page.PrintToPDFRequest
import com.mkobit.cdp.domain.page.ReloadRequest
import com.mkobit.cdp.domain.page.RemoveScriptToEvaluateOnLoadRequest
import com.mkobit.cdp.domain.page.RemoveScriptToEvaluateOnNewDocumentRequest
import com.mkobit.cdp.domain.page.ScreencastFrameAckRequest
import com.mkobit.cdp.domain.page.SearchInResourceReply
import com.mkobit.cdp.domain.page.SearchInResourceRequest
import com.mkobit.cdp.domain.page.SetAdBlockingEnabledRequest
import com.mkobit.cdp.domain.page.SetBypassCSPRequest
import com.mkobit.cdp.domain.page.SetDeviceMetricsOverrideRequest
import com.mkobit.cdp.domain.page.SetDeviceOrientationOverrideRequest
import com.mkobit.cdp.domain.page.SetDocumentContentRequest
import com.mkobit.cdp.domain.page.SetDownloadBehaviorRequest
import com.mkobit.cdp.domain.page.SetFontFamiliesRequest
import com.mkobit.cdp.domain.page.SetFontSizesRequest
import com.mkobit.cdp.domain.page.SetGeolocationOverrideRequest
import com.mkobit.cdp.domain.page.SetLifecycleEventsEnabledRequest
import com.mkobit.cdp.domain.page.SetProduceCompilationCacheRequest
import com.mkobit.cdp.domain.page.SetTouchEmulationEnabledRequest
import com.mkobit.cdp.domain.page.SetWebLifecycleStateRequest
import com.mkobit.cdp.domain.page.StartScreencastRequest
import io.ktor.http.cio.websocket.WebSocketSession
import java.util.concurrent.atomic.AtomicLong

internal class KtorClientWebsocketPageDomain(
  session: WebSocketSession,
  objectMapper: ObjectMapper,
  requestIdGenerator: AtomicLong
) : BaseKtorWebsocketDomain(session, objectMapper, requestIdGenerator), PageDomain {

  override suspend fun addScriptToEvaluateOnLoad(request: AddScriptToEvaluateOnLoadRequest): AddScriptToEvaluateOnLoadReply =
    sendAndAwait(request)

  override suspend fun addScriptToEvaluateOnNewDocument(request: AddScriptToEvaluateOnNewDocumentRequest): AddScriptToEvaluateOnNewDocumentReply =
    sendAndAwait(request)

  override suspend fun bringToFront() = sendAndAwait<Unit>()

  override suspend fun captureScreenshot(request: CaptureScreenshotRequest): CaptureScreenshotReply = sendAndAwait(request)

  override suspend fun captureSnapshot(request: CaptureSnapshotRequest): CaptureSnapshotReply = sendAndAwait(request)

  override suspend fun clearDeviceMetricsOverride() = sendAndAwait<Unit>()

  override suspend fun clearDeviceOrientationOverride() = sendAndAwait<Unit>()

  override suspend fun clearGeolocationOverride() = sendAndAwait<Unit>()

  override suspend fun createIsolatedWorld(request: CreateIsolatedWorldRequest): CreateIsolatedWorldReply = sendAndAwait(request)

  override suspend fun deleteCookie(request: DeleteCookieRequest) = sendAndAwait<Unit>(request)

  override suspend fun disable() = sendAndAwait<Unit>()

  override suspend fun enable() = sendAndAwait<Unit>()

  override suspend fun getAppManifest(): GetAppManifestReply = sendAndAwait()

  override suspend fun getCookies(): GetCookiesReply = sendAndAwait()

  override suspend fun getFrameTree(): GetFrameTreeReply = sendAndAwait()

  override suspend fun getLayoutMetrics(): GetLayoutMetricsReply = sendAndAwait()

  override suspend fun getNavigationHistory(): GetNavigationHistoryReply = sendAndAwait()

  override suspend fun getResourceContent(request: GetResourceContentRequest): GetResourceContentReply = sendAndAwait(request)

  override suspend fun getResourceTree(): GetResourceTreeReply = sendAndAwait()

  override suspend fun handleJavaScriptDialog(request: HandleJavaScriptDialogRequest) = sendAndAwait<Unit>(request)

  override suspend fun navigate(request: NavigateRequest): NavigateReply = sendAndAwait(request)

  override suspend fun navigateToHistoryEntry(request: NavigateToHistoryEntryRequest) = sendAndAwait<Unit>(request)

  override suspend fun printToPDF(request: PrintToPDFRequest): PrintToPDFReply = sendAndAwait(request)

  override suspend fun reload(request: ReloadRequest) = sendAndAwait<Unit>(request)

  override suspend fun removeScriptToEvaluateOnLoad(request: RemoveScriptToEvaluateOnLoadRequest) = sendAndAwait<Unit>(request)

  override suspend fun removeScriptToEvaluateOnNewDocument(request: RemoveScriptToEvaluateOnNewDocumentRequest) = sendAndAwait<Unit>(request)

  override suspend fun requestAppBanner() = sendAndAwait<Unit>()

  override suspend fun screencastFrameAck(request: ScreencastFrameAckRequest) = sendAndAwait<Unit>(request)

  override suspend fun searchInResource(request: SearchInResourceRequest): SearchInResourceReply = sendAndAwait(request)

  override suspend fun setAdBlockingEnabled(request: SetAdBlockingEnabledRequest) = sendAndAwait<Unit>(request)

  override suspend fun setBypassCSP(request: SetBypassCSPRequest) = sendAndAwait<Unit>(request)

  override suspend fun setDeviceMetricsOverride(request: SetDeviceMetricsOverrideRequest) = sendAndAwait<Unit>(request)

  override suspend fun setDeviceOrientationOverride(request: SetDeviceOrientationOverrideRequest) = sendAndAwait<Unit>(request)

  override suspend fun setFontFamilies(request: SetFontFamiliesRequest) = sendAndAwait<Unit>(request)

  override suspend fun setFontSizes(request: SetFontSizesRequest) = sendAndAwait<Unit>(request)

  override suspend fun setDocumentContent(request: SetDocumentContentRequest) = sendAndAwait<Unit>(request)

  override suspend fun setDownloadBehavior(request: SetDownloadBehaviorRequest) = sendAndAwait<Unit>(request)

  override suspend fun setGeolocationOverride(request: SetGeolocationOverrideRequest) = sendAndAwait<Unit>(request)

  override suspend fun setLifecycleEventsEnabled(request: SetLifecycleEventsEnabledRequest) = sendAndAwait<Unit>(request)

  override suspend fun setTouchEmulationEnabled(request: SetTouchEmulationEnabledRequest) = sendAndAwait<Unit>(request)

  override suspend fun startScreencast(request: StartScreencastRequest) = sendAndAwait<Unit>(request)

  override suspend fun stopLoading() = sendAndAwait<Unit>()

  override suspend fun crash() = sendAndAwait<Unit>()

  override suspend fun close() = sendAndAwait<Unit>()

  override suspend fun setWebLifecycleState(request: SetWebLifecycleStateRequest) = sendAndAwait<Unit>(request)

  override suspend fun stopScreencast() = sendAndAwait<Unit>()

  override suspend fun setProduceCompilationCache(request: SetProduceCompilationCacheRequest) = sendAndAwait<Unit>(request)

  override suspend fun addCompilationCache(request: AddCompilationCacheRequest) = sendAndAwait<Unit>(request)

  override suspend fun clearCompilationCache() = sendAndAwait<Unit>()

  override suspend fun generateTestReport(request: GenerateTestReportRequest) = sendAndAwait<Unit>(request)
}
