package com.mkobit.chickendinner.chrome.domain.page

import com.fasterxml.jackson.annotation.JsonProperty
import com.mkobit.chickendinner.chrome.domain.DebugProtocolMethod

typealias FrameId = String
typealias LoaderId = String

interface PageDomain {
  suspend fun 
}

data class NavigateRequest(
    val url: String,
    val referrer: String? = null,
    val transitionType: TransitionType? = null,
    val frameId: FrameId? = null
) : DebugProtocolMethod {
  override val method: String
    get() = "Page.navigate"

}

data class NavigateResponse(
    val frameId: FrameId,
    val loaderId: LoaderId,
    val errorText: String?
)

enum class TransitionType {
  @JsonProperty("link") LINK,
  @JsonProperty("typed") TYPED,
  @JsonProperty("auto_bookmark") AUTO_BOOKMARK,
  @JsonProperty("auto_subframe") AUTO_SUBFRAME,
  @JsonProperty("manual_subframe") MANUAL_SUBFRAME,
  @JsonProperty("generated") GENERATED,
  @JsonProperty("auto_toplevel") AUTO_TOPLEVEL,
  @JsonProperty("form_submit") FORM_SUBMIT,
  @JsonProperty("reload") RELOAD,
  @JsonProperty("keyword") KEYWORD,
  @JsonProperty("keyword_generated") KEYWORD_GENERATED,
  @JsonProperty("other") OTHER;
}
