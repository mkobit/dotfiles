package com.mkobit.chickendinner.chrome

import com.fasterxml.jackson.annotation.JsonProperty

data class ProtocolVersion(
  @get:JsonProperty("Browser") val browser: String,
  @get:JsonProperty("Protocol-Version") val protocolVersion: String,
  @get:JsonProperty("User-Agent") val userAgent: String,
  @get:JsonProperty("V8-Version") val v8Version: String,
  @get:JsonProperty("WebKit-Version") val webKitVersion: String,
  val webSocketDebuggerUrl: String
)
