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
sealed class PageInfo(
  val description: String,
  val devtoolsFrontendUrl: String,
  val id: String,
  val title: String,
  val url: String,
  val webSocketDebuggerUrl: String
) {
  class BackGroundPageInfo(
    description: String,
    devtoolsFrontendUrl: String,
    id: String,
    title: String,
    url: String,
    webSocketDebuggerUrl: String
  ) : PageInfo(description, devtoolsFrontendUrl, id, title, url, webSocketDebuggerUrl)

  class WebPageInfo(
    description: String,
    devtoolsFrontendUrl: String,
    id: String,
    title: String,
    url: String,
    webSocketDebuggerUrl: String,
    val faviconUrl: String?
  ) : PageInfo(description, devtoolsFrontendUrl, id, title, url, webSocketDebuggerUrl)

  class IframePageInfo(
    description: String,
    devtoolsFrontendUrl: String,
    id: String,
    title: String,
    url: String,
    webSocketDebuggerUrl: String,
    val faviconUrl: String?,
    val parentId: String
  ) : PageInfo(description, devtoolsFrontendUrl, id, title, url, webSocketDebuggerUrl)

  class ServiceWorkerPageInfo(
    description: String,
    devtoolsFrontendUrl: String,
    id: String,
    title: String,
    url: String,
    webSocketDebuggerUrl: String
  ) : PageInfo(description, devtoolsFrontendUrl, id, title, url, webSocketDebuggerUrl)

  class OtherPageInfo(
    description: String,
    devtoolsFrontendUrl: String,
    id: String,
    title: String,
    url: String,
    webSocketDebuggerUrl: String
  ) : PageInfo(description, devtoolsFrontendUrl, id, title, url, webSocketDebuggerUrl)
}
