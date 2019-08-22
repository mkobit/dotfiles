package com.mkobit.chickendinner.chrome.internal.cdp

import com.mkobit.chickendinner.chrome.PageInfo
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach
import org.testcontainers.junit.jupiter.Container
import org.testcontainers.junit.jupiter.Testcontainers
import testsupport.container.ChromeContainer

@Testcontainers
internal class KtorClientWebsocketPageTest {

  companion object {
    @Container
    @JvmStatic
    private var chrome: ChromeContainer = ChromeContainer()
  }

  private lateinit var page: PageInfo
  private lateinit var pageDomain: KtorClientWebsocketPageDomain

  @BeforeEach
  internal fun setUp() {
    TODO("not implemented") // To change body of created functions use File | Settings | File Templates.
  }

  @AfterEach
  internal fun tearDown() {
    TODO("not implemented") // To change body of created functions use File | Settings | File Templates.
  }
}
