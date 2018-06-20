package com.mkobit.chickendinner.chrome.domain.browser

import com.mkobit.chickendinner.chrome.domain.DebugProtocolMethod

@DebugProtocolMethod("Browser.close")
class CloseBrowser

@DebugProtocolMethod("Browser.getVersion")
class GetBrowserVersion

data class BrowserVersion(
    val protocolVersion: String,
    val product: String,
    val revision: String,
    val userAgent: String,
    val jsVersion: String
)
