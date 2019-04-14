package com.mkobit.chickendinner.amazon

import org.jsoup.Jsoup

class GiveawayEmailParser {
  fun parse(emailText: String): List<GiveawaySource> {
    val document = Jsoup.parse(emailText)
    return document
      .select("a > img:not([width='1']):not([alt='Gmail']):not([src*='header']):not([alt='Amazon.com'])")
      .asSequence()
      .map { it.parent() }
      .map { it.attr("href") }
      .map { GiveawaySource(it) }
      .toList()
  }
}
