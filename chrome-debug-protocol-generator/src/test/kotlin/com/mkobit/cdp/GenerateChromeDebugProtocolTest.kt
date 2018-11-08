package com.mkobit.cdp

import com.google.common.io.Resources
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.extension.ExtendWith
import org.junitpioneer.jupiter.TempDirectory
import java.nio.file.Files
import java.nio.file.Path

@ExtendWith(TempDirectory::class)
internal class GenerateChromeDebugProtocolTest {

  @Test
  internal fun `generate 1_3`(
      @TempDirectory.TempDir generationDirectory: Path,
      @TempDirectory.TempDir tempDirectory: Path
  ) {
    val jsonFileName = "browser_protocol-1.3.json"
    val tempJson = tempDirectory.resolve(jsonFileName)
    Files.write(tempJson, Resources.readLines(Resources.getResource("browser_protocol-1.3.json"), Charsets.UTF_8))

    generateChromeDebugProtocol(
        ChromeDebugProtocolGenerationRequest("com.mkobit.chromedebugprotocol", tempJson, generationDirectory)
    )
  }
}
