package com.mkobit.chickendinner.chrome

import assertk.assert
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.databind.SerializerProvider
import com.fasterxml.jackson.databind.module.SimpleModule
import com.fasterxml.jackson.databind.ser.BeanSerializerModifier
import com.fasterxml.jackson.databind.ser.ResolvableSerializer
import com.fasterxml.jackson.module.kotlin.readValue
import com.fasterxml.jackson.module.kotlin.registerKotlinModule
import com.google.common.io.Resources
import org.junit.jupiter.api.Test

internal class PageInfoSerDeTest {
  @Test
  internal fun `can deserialize into PageInfo types`() {
    val mapper = ObjectMapper().registerKotlinModule()
    assert {
      mapper.readValue<List<PageInfo>>(Resources.getResource("com/mkobit/chickendinner/chrome/chrome-debugger-view.json"))
    }.returnedValue {
      // no exception
    }
  }
}
