package com.mkobit.chickendinner.chrome.internal.cdp

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import com.fasterxml.jackson.module.kotlin.treeToValue
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
import com.mkobit.chickendinner.chrome.RequestFrame
import com.mkobit.chickendinner.chrome.ResponseFrame
import io.ktor.http.cio.websocket.Frame as WebsocketFrame
import io.ktor.http.cio.websocket.WebSocketSession
import kotlinx.coroutines.channels.filter
import kotlinx.coroutines.channels.first
import kotlinx.coroutines.channels.map
import java.util.concurrent.atomic.AtomicLong

internal class KtorClientWebsocketPageDomain(
  private val session: WebSocketSession,
  private val objectMapper: ObjectMapper,
  private val requestIdGenerator: AtomicLong

) : BaseKtorWebsocketDomain(session, objectMapper, requestIdGenerator), PageDomain {
  override suspend fun addScriptToEvaluateOnLoad(request: AddScriptToEvaluateOnLoadRequest): AddScriptToEvaluateOnLoadReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun addScriptToEvaluateOnNewDocument(request: AddScriptToEvaluateOnNewDocumentRequest): AddScriptToEvaluateOnNewDocumentReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun bringToFront() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun captureScreenshot(request: CaptureScreenshotRequest): CaptureScreenshotReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun captureSnapshot(request: CaptureSnapshotRequest): CaptureSnapshotReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun clearDeviceMetricsOverride() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun clearDeviceOrientationOverride() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun clearGeolocationOverride() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun createIsolatedWorld(request: CreateIsolatedWorldRequest): CreateIsolatedWorldReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun deleteCookie(request: DeleteCookieRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun disable() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun enable() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun getAppManifest(): GetAppManifestReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun getCookies(): GetCookiesReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun getFrameTree(): GetFrameTreeReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun getLayoutMetrics(): GetLayoutMetricsReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun getNavigationHistory(): GetNavigationHistoryReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun getResourceContent(request: GetResourceContentRequest): GetResourceContentReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun getResourceTree(): GetResourceTreeReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun handleJavaScriptDialog(request: HandleJavaScriptDialogRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun navigate(request: NavigateRequest): NavigateReply = sendAndAwait(request)

  override suspend fun navigateToHistoryEntry(request: NavigateToHistoryEntryRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun printToPDF(request: PrintToPDFRequest): PrintToPDFReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun reload(request: ReloadRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun removeScriptToEvaluateOnLoad(request: RemoveScriptToEvaluateOnLoadRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun removeScriptToEvaluateOnNewDocument(request: RemoveScriptToEvaluateOnNewDocumentRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun requestAppBanner() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun screencastFrameAck(request: ScreencastFrameAckRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun searchInResource(request: SearchInResourceRequest): SearchInResourceReply {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun setAdBlockingEnabled(request: SetAdBlockingEnabledRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun setBypassCSP(request: SetBypassCSPRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun setDeviceMetricsOverride(request: SetDeviceMetricsOverrideRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun setDeviceOrientationOverride(request: SetDeviceOrientationOverrideRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun setFontFamilies(request: SetFontFamiliesRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun setFontSizes(request: SetFontSizesRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun setDocumentContent(request: SetDocumentContentRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun setDownloadBehavior(request: SetDownloadBehaviorRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun setGeolocationOverride(request: SetGeolocationOverrideRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun setLifecycleEventsEnabled(request: SetLifecycleEventsEnabledRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun setTouchEmulationEnabled(request: SetTouchEmulationEnabledRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun startScreencast(request: StartScreencastRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun stopLoading() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun crash() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun close() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun setWebLifecycleState(request: SetWebLifecycleStateRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun stopScreencast() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun setProduceCompilationCache(request: SetProduceCompilationCacheRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun addCompilationCache(request: AddCompilationCacheRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun clearCompilationCache() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  override suspend fun generateTestReport(request: GenerateTestReportRequest) {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }
}
