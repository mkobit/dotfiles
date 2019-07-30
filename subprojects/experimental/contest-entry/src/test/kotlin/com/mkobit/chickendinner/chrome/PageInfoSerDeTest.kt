package com.mkobit.chickendinner.chrome

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import com.fasterxml.jackson.module.kotlin.registerKotlinModule
import com.google.common.io.Resources
import org.junit.jupiter.api.Test
import strikt.api.expectCatching
import strikt.assertions.succeeded

internal class PageInfoSerDeTest {
  @Test
  internal fun `can deserialize into PageInfo types`() {
    val mapper = ObjectMapper().registerKotlinModule()
    expectCatching {
      mapper.readValue<List<PageInfo>>(Resources.getResource("com/mkobit/chickendinner/chrome/chrome-debugger-view.json"))
    }.succeeded()
  }
}
