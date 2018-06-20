package com.mkobit.chickendinner.chrome

import assertk.assert
import assertk.assertions.isEqualTo
import org.junit.jupiter.api.Test
import testsupport.assertk.isNone
import testsupport.assertk.isSome

internal class ChromeTest {
  @Test internal fun `can determine port from error output that includes log message`() {
    val option = determineChromePortFromLog("""
      [3778:3905:0425/091509.954814:ERROR:in_progress_cache_impl.cc(93)] Could not read download entries from file because there was a read failure.

      DevTools listening on ws://127.0.0.1:43507/devtools/browser/fa168e14-c4bb-4551-b701-4e333ecc93a9
    """.trimIndent())

    assert(option).isSome {
      it.isEqualTo(43507)
    }
  }

  @Test internal fun `cannot determine port from error output that does not include log message`() {
    val option = determineChromePortFromLog("""
      [3778:3905:0425/091509.954814:ERROR:in_progress_cache_impl.cc(93)] Could not read download entries from file because there was a read failure.
    """.trimIndent())

    assert(option).isNone()
  }
}
