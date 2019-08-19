package com.mkobit.chickendinner.chrome

import com.fasterxml.jackson.annotation.JsonSubTypes
import com.fasterxml.jackson.annotation.JsonTypeInfo

@JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type", include = JsonTypeInfo.As.PROPERTY)
@JsonSubTypes(value = [
  JsonSubTypes.Type(PageInfo.BackGroundPageInfo::class, name = "background_page"),
  JsonSubTypes.Type(PageInfo.WebPageInfo::class, name = "page"),
  JsonSubTypes.Type(PageInfo.IframePageInfo::class, name = "iframe"),
  JsonSubTypes.Type(PageInfo.ServiceWorkerPageInfo::class, name = "service_worker"),
  JsonSubTypes.Type(PageInfo.OtherPageInfo::class, name = "other")
])
sealed class PageInfo {
  abstract val description: String
  abstract val devtoolsFrontendUrl: String
  abstract val id: String
  abstract val title: String
  abstract val url: String
  abstract val webSocketDebuggerUrl: String

  data class BackGroundPageInfo(
    override val description: String,
    override val devtoolsFrontendUrl: String,
    override val id: String,
    override val title: String,
    override val url: String,
    override val webSocketDebuggerUrl: String
  ) : PageInfo()

  data class WebPageInfo(
    override val description: String,
    override val devtoolsFrontendUrl: String,
    override val id: String,
    override val title: String,
    override val url: String,
    override val webSocketDebuggerUrl: String,
    val faviconUrl: String?
  ) : PageInfo()

  data class IframePageInfo(
    override val description: String,
    override val devtoolsFrontendUrl: String,
    override val id: String,
    override val title: String,
    override val url: String,
    override val webSocketDebuggerUrl: String,
    val faviconUrl: String?,
    val parentId: String
  ) : PageInfo()

  data class ServiceWorkerPageInfo(
    override val description: String,
    override val devtoolsFrontendUrl: String,
    override val id: String,
    override val title: String,
    override val url: String,
    override val webSocketDebuggerUrl: String
  ) : PageInfo()

  data class OtherPageInfo(
    override val description: String,
    override val devtoolsFrontendUrl: String,
    override val id: String,
    override val title: String,
    override val url: String,
    override val webSocketDebuggerUrl: String
  ) : PageInfo()
}
