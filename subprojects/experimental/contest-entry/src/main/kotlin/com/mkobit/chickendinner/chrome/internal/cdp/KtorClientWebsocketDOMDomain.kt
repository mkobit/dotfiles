package com.mkobit.chickendinner.chrome.internal.cdp

import com.fasterxml.jackson.databind.ObjectMapper
import com.mkobit.cdp.domain.dom.CollectClassNamesFromSubtreeReply
import com.mkobit.cdp.domain.dom.CollectClassNamesFromSubtreeRequest
import com.mkobit.cdp.domain.dom.CopyToReply
import com.mkobit.cdp.domain.dom.CopyToRequest
import com.mkobit.cdp.domain.dom.DOMDomain
import com.mkobit.cdp.domain.dom.DescribeNodeReply
import com.mkobit.cdp.domain.dom.DescribeNodeRequest
import com.mkobit.cdp.domain.dom.DiscardSearchResultsRequest
import com.mkobit.cdp.domain.dom.FocusRequest
import com.mkobit.cdp.domain.dom.GetAttributesReply
import com.mkobit.cdp.domain.dom.GetAttributesRequest
import com.mkobit.cdp.domain.dom.GetBoxModelReply
import com.mkobit.cdp.domain.dom.GetBoxModelRequest
import com.mkobit.cdp.domain.dom.GetContentQuadsReply
import com.mkobit.cdp.domain.dom.GetContentQuadsRequest
import com.mkobit.cdp.domain.dom.GetDocumentReply
import com.mkobit.cdp.domain.dom.GetDocumentRequest
import com.mkobit.cdp.domain.dom.GetFlattenedDocumentReply
import com.mkobit.cdp.domain.dom.GetFlattenedDocumentRequest
import com.mkobit.cdp.domain.dom.GetFrameOwnerReply
import com.mkobit.cdp.domain.dom.GetFrameOwnerRequest
import com.mkobit.cdp.domain.dom.GetNodeForLocationReply
import com.mkobit.cdp.domain.dom.GetNodeForLocationRequest
import com.mkobit.cdp.domain.dom.GetOuterHTMLReply
import com.mkobit.cdp.domain.dom.GetOuterHTMLRequest
import com.mkobit.cdp.domain.dom.GetRelayoutBoundaryReply
import com.mkobit.cdp.domain.dom.GetRelayoutBoundaryRequest
import com.mkobit.cdp.domain.dom.GetSearchResultsReply
import com.mkobit.cdp.domain.dom.GetSearchResultsRequest
import com.mkobit.cdp.domain.dom.MoveToReply
import com.mkobit.cdp.domain.dom.MoveToRequest
import com.mkobit.cdp.domain.dom.PerformSearchReply
import com.mkobit.cdp.domain.dom.PerformSearchRequest
import com.mkobit.cdp.domain.dom.PushNodeByPathToFrontendReply
import com.mkobit.cdp.domain.dom.PushNodeByPathToFrontendRequest
import com.mkobit.cdp.domain.dom.PushNodesByBackendIdsToFrontendReply
import com.mkobit.cdp.domain.dom.PushNodesByBackendIdsToFrontendRequest
import com.mkobit.cdp.domain.dom.QuerySelectorAllReply
import com.mkobit.cdp.domain.dom.QuerySelectorAllRequest
import com.mkobit.cdp.domain.dom.QuerySelectorReply
import com.mkobit.cdp.domain.dom.QuerySelectorRequest
import com.mkobit.cdp.domain.dom.RemoveAttributeRequest
import com.mkobit.cdp.domain.dom.RemoveNodeRequest
import com.mkobit.cdp.domain.dom.RequestChildNodesRequest
import com.mkobit.cdp.domain.dom.RequestNodeReply
import com.mkobit.cdp.domain.dom.RequestNodeRequest
import com.mkobit.cdp.domain.dom.ResolveNodeReply
import com.mkobit.cdp.domain.dom.ResolveNodeRequest
import com.mkobit.cdp.domain.dom.SetAttributeValueRequest
import com.mkobit.cdp.domain.dom.SetAttributesAsTextRequest
import com.mkobit.cdp.domain.dom.SetFileInputFilesRequest
import com.mkobit.cdp.domain.dom.SetInspectedNodeRequest
import com.mkobit.cdp.domain.dom.SetNodeNameReply
import com.mkobit.cdp.domain.dom.SetNodeNameRequest
import com.mkobit.cdp.domain.dom.SetNodeValueRequest
import com.mkobit.cdp.domain.dom.SetOuterHTMLRequest
import io.ktor.http.cio.websocket.WebSocketSession
import java.util.concurrent.atomic.AtomicLong

internal class KtorClientWebsocketDOMDomain(
  session: WebSocketSession,
  objectMapper: ObjectMapper,
  requestIdGenerator: AtomicLong
) : BaseKtorWebsocketDomain(session, objectMapper, requestIdGenerator), DOMDomain {

  override suspend fun collectClassNamesFromSubtree(request: CollectClassNamesFromSubtreeRequest): CollectClassNamesFromSubtreeReply =
    sendAndAwait(request)

  override suspend fun copyTo(request: CopyToRequest): CopyToReply = sendAndAwait(request)

  override suspend fun describeNode(request: DescribeNodeRequest): DescribeNodeReply = sendAndAwait(request)

  override suspend fun disable() = sendAndAwait<Unit>()

  override suspend fun discardSearchResults(request: DiscardSearchResultsRequest) = sendAndAwait<Unit>(request)

  override suspend fun enable() = sendAndAwait<Unit>()

  override suspend fun focus(request: FocusRequest) = sendAndAwait<Unit>(request)

  override suspend fun getAttributes(request: GetAttributesRequest): GetAttributesReply = sendAndAwait(request)

  override suspend fun getBoxModel(request: GetBoxModelRequest): GetBoxModelReply = sendAndAwait(request)

  override suspend fun getContentQuads(request: GetContentQuadsRequest): GetContentQuadsReply = sendAndAwait(request)

  override suspend fun getDocument(request: GetDocumentRequest): GetDocumentReply = sendAndAwait(request)

  override suspend fun getFlattenedDocument(request: GetFlattenedDocumentRequest): GetFlattenedDocumentReply = sendAndAwait(request)

  override suspend fun getNodeForLocation(request: GetNodeForLocationRequest): GetNodeForLocationReply = sendAndAwait(request)

  override suspend fun getOuterHTML(request: GetOuterHTMLRequest): GetOuterHTMLReply = sendAndAwait(request)

  override suspend fun getRelayoutBoundary(request: GetRelayoutBoundaryRequest): GetRelayoutBoundaryReply = sendAndAwait(request)

  override suspend fun getSearchResults(request: GetSearchResultsRequest): GetSearchResultsReply = sendAndAwait(request)

  override suspend fun hideHighlight() = sendAndAwait<Unit>()

  override suspend fun highlightNode() = sendAndAwait<Unit>()

  override suspend fun highlightRect() = sendAndAwait<Unit>()

  override suspend fun markUndoableState() = sendAndAwait<Unit>()

  override suspend fun moveTo(request: MoveToRequest): MoveToReply = sendAndAwait(request)

  override suspend fun performSearch(request: PerformSearchRequest): PerformSearchReply = sendAndAwait(request)

  override suspend fun pushNodeByPathToFrontend(request: PushNodeByPathToFrontendRequest): PushNodeByPathToFrontendReply =
    sendAndAwait(request)

  override suspend fun pushNodesByBackendIdsToFrontend(request: PushNodesByBackendIdsToFrontendRequest): PushNodesByBackendIdsToFrontendReply =
    sendAndAwait(request)

  override suspend fun querySelector(request: QuerySelectorRequest): QuerySelectorReply = sendAndAwait(request)

  override suspend fun querySelectorAll(request: QuerySelectorAllRequest): QuerySelectorAllReply = sendAndAwait(request)

  override suspend fun redo() = sendAndAwait<Unit>()

  override suspend fun removeAttribute(request: RemoveAttributeRequest) = sendAndAwait<Unit>(request)

  override suspend fun removeNode(request: RemoveNodeRequest) = sendAndAwait<Unit>(request)

  override suspend fun requestChildNodes(request: RequestChildNodesRequest) = sendAndAwait<Unit>(request)

  override suspend fun requestNode(request: RequestNodeRequest): RequestNodeReply = sendAndAwait(request)

  override suspend fun resolveNode(request: ResolveNodeRequest): ResolveNodeReply = sendAndAwait(request)

  override suspend fun setAttributeValue(request: SetAttributeValueRequest) = sendAndAwait<Unit>(request)

  override suspend fun setAttributesAsText(request: SetAttributesAsTextRequest) = sendAndAwait<Unit>(request)

  override suspend fun setFileInputFiles(request: SetFileInputFilesRequest) = sendAndAwait<Unit>(request)

  override suspend fun setInspectedNode(request: SetInspectedNodeRequest) = sendAndAwait<Unit>(request)

  override suspend fun setNodeName(request: SetNodeNameRequest): SetNodeNameReply = sendAndAwait(request)

  override suspend fun setNodeValue(request: SetNodeValueRequest) = sendAndAwait<Unit>(request)

  override suspend fun setOuterHTML(request: SetOuterHTMLRequest) = sendAndAwait<Unit>(request)

  override suspend fun undo() = sendAndAwait<Unit>()

  override suspend fun getFrameOwner(request: GetFrameOwnerRequest): GetFrameOwnerReply = sendAndAwait(request)
}
