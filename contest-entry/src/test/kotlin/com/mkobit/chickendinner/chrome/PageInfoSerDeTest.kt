package com.mkobit.chickendinner.chrome

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import com.fasterxml.jackson.module.kotlin.registerKotlinModule
import com.google.common.io.Resources
import org.junit.jupiter.api.Test
import strikt.api.catching
import strikt.api.expectThat
import strikt.assertions.isNotNull
import strikt.assertions.isNull

internal class PageInfoSerDeTest {
  @Test
  internal fun `can deserialize into PageInfo types`() {
    val mapper = ObjectMapper().registerKotlinModule()
    expectThat(catching {
      mapper.readValue<List<PageInfo>>(Resources.getResource("com/mkobit/chickendinner/chrome/chrome-debugger-view.json"))
    }).isNull()
  }
}
