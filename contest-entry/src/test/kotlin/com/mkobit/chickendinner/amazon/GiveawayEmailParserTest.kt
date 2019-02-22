package com.mkobit.chickendinner.amazon

import com.google.common.io.Resources
import org.jsoup.Jsoup
import org.junit.jupiter.api.Test

internal class GiveawayEmailParserTest {
  @Test
  internal fun `can parse an email`() {
    val emailText = Resources.getResource("com/mkobit/chickendinner/amazon/giveaway-emails/sanitized-email.html").readText(Charsets.UTF_8)
    val document = Jsoup.parse(emailText)
    val aHrefNodes = document.select("a[href]")
    val giveawayAHrefNodes = aHrefNodes.filter {
      val a: String = it.attr("href")
      a.contains("amazon.com")
    }
    println(document)
  }
}
