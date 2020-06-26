package com.mkobit.chickendinner.chrome

import io.ktor.client.HttpClient
import io.ktor.client.engine.cio.CIO
import io.ktor.client.features.ClientRequestException
import io.ktor.client.features.json.JacksonSerializer
import io.ktor.client.features.json.JsonFeature
import io.ktor.client.response.readText
import io.ktor.http.HttpStatusCode
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.runBlockingTest
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Disabled
import org.junit.jupiter.api.Order
import org.junit.jupiter.api.Test
import org.testcontainers.junit.jupiter.Container
import org.testcontainers.junit.jupiter.Testcontainers
import strikt.api.expectCatching
import strikt.api.expectThat
import strikt.assertions.contains
import strikt.assertions.doesNotContain
import strikt.assertions.failed
import strikt.assertions.isA
import strikt.assertions.isEqualTo
import strikt.assertions.map
import strikt.assertions.succeeded
import testsupport.container.ChromeContainer
import testsupport.junit.Stepwise

@Disabled("Disabled until test containers issued figured out")
@Testcontainers
@Stepwise
internal class ChromeDebuggerTest {

  companion object {
    @Container
    @JvmStatic
    private var chrome: ChromeContainer = ChromeContainer()
  }

  private lateinit var debugger: ChromeDebugger

  private lateinit var page1: PageInfo
  private lateinit var page2: PageInfo

  @BeforeEach
  internal fun setUp() {
    debugger = ChromeDebugger(chrome.debugProtocolPort, HttpClient(CIO) {
      install(JsonFeature) {
        serializer = JacksonSerializer()
      }
    })
  }

  @Test
  internal fun version() =
    runBlockingTest {
      expectCatching { debugger.version() }.succeeded()
    }

  @Test
  internal fun `activate invalid page`() =
    //    runBlockingTest {
    runBlocking {
      val targetId = "1234-invalid"
      expectCatching {
        debugger.activate(targetId)
      }.failed()
        .isA<ClientRequestException>()
        .get { response }
        .and {
          get { status }.isEqualTo(HttpStatusCode.NotFound)
          get { runBlocking { readText() } }.isEqualTo("No such target id: $targetId")
        }
      Unit
    }

  @Test
  internal fun `close invalid page`() =
    //    runBlockingTest {
    runBlocking {
      val targetId = "5678-invalid"
      expectCatching {
        debugger.close(targetId)
      }.failed()
        .isA<ClientRequestException>()
        .get { response }
        .and {
          get { status }.isEqualTo(HttpStatusCode.NotFound)
          get { runBlocking { readText() } }.isEqualTo("No such target id: $targetId")
        }
      Unit
    }

  @Test
  @Order(1)
  internal fun `new pages`() =
    //    runBlockingTest {
    runBlocking {
      expectCatching {
        page1 = debugger.newPage("about://chrome")
        page2 = debugger.newPage("about://chrome")
      }.succeeded()
      Unit
    }

  @Test
  @Order(2)
  internal fun `all opened pages`() =
//    runBlockingTest {
    runBlocking {
      val pages = debugger.openedPages()
      expectThat(debugger.openedPages()) {
        map { it.webSocketDebuggerUrl }.contains(page1.webSocketDebuggerUrl, page2.webSocketDebuggerUrl)
        map { it.id }.contains(page1.id, page2.id)
      }
      Unit
    }

  @Test
  @Order(3)
  internal fun `activate a valid page`() =
//    runBlockingTest {
    runBlocking {
      expectThat(debugger.activate(page1))
        .isEqualTo("Target activated")
      Unit
    }

  @Test
  @Order(4)
  internal fun `close a page`() =
    //    runBlockingTest {
    runBlocking {
      expectThat(debugger.close(page2))
        .isEqualTo("Target is closing")
      Unit
    }

  @Test
  @Order(5)
  internal fun `list opened pages after closing one`() =
    //    runBlockingTest {
    runBlocking {
      expectThat(debugger.openedPages())
        .doesNotContain(page2)
      Unit
    }

  @Test
  @Order(6)
  internal fun `close last open page by Id`() =
    //    runBlockingTest {
    runBlocking {
      expectThat(debugger.close(page1.id))
        .isEqualTo("Target is closing")
      Unit
    }

  @Test
  @Order(7)
  internal fun `list opened pages`() =
    //    runBlockingTest {
    runBlocking {
      expectThat(debugger.openedPages())
        .map { it.id }.doesNotContain(page1.id, page2.id)
      Unit
    }
}
