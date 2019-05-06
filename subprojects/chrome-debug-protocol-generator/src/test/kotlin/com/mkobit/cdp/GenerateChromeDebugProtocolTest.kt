package com.mkobit.cdp

import com.google.common.io.Resources
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import java.nio.file.Files
import java.nio.file.Path

internal class GenerateChromeDebugProtocolTest {

  @Test
  internal fun `generate 1_3`(
      @TempDir generationDirectory: Path,
      @TempDir tempDirectory: Path
  ) {
    val browserFileName = "browser_protocol-1.3.json"
    val jsFileName = "js_protocol-1.3.json"
    val tempBrowserJson = tempDirectory.resolve(browserFileName)
    val tempJsProtocolJson = tempDirectory.resolve(browserFileName)
    Files.write(tempBrowserJson, Resources.readLines(Resources.getResource(browserFileName), Charsets.UTF_8))
    Files.write(tempJsProtocolJson, Resources.readLines(Resources.getResource(jsFileName), Charsets.UTF_8))

    generateChromeDebugProtocol(
        ChromeDebugProtocolGenerationRequest("com.mkobit.chromedebugprotocol", listOf(tempBrowserJson, tempJsProtocolJson), generationDirectory)
    )
  }
}
