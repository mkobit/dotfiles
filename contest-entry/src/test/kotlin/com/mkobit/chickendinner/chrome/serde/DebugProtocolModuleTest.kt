package com.mkobit.chickendinner.chrome.serde

import assertk.assert
import assertk.assertions.isEqualTo
import com.fasterxml.jackson.databind.BeanDescription
import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.JsonSerializer
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.databind.SerializationConfig
import com.fasterxml.jackson.databind.module.SimpleModule
import com.fasterxml.jackson.databind.ser.BeanSerializerModifier
import com.fasterxml.jackson.module.kotlin.readValue
import com.fasterxml.jackson.module.kotlin.registerKotlinModule
import com.mkobit.chickendinner.chrome.domain.DebugProtocolMethod
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Disabled
import org.junit.jupiter.api.Test


internal class DebugProtocolModuleTest {
  private lateinit var mapper: ObjectMapper

  @BeforeEach
  internal fun setUp() {
    mapper = ObjectMapper()
        .registerKotlinModule()
//        .registerModule(DebugProtocolModule())
    val module = SimpleModule()
    module.setSerializerModifier(object : BeanSerializerModifier() {
      override fun modifySerializer(
          config: SerializationConfig,
          beanDesc: BeanDescription,
          serializer: JsonSerializer<*>
      ): JsonSerializer<*> {
        val method: DebugProtocolMethod? = beanDesc.classAnnotations[DebugProtocolMethod::class.java]
        return if (method != null) {
          DebugProtocolMethodJsonSerializer(serializer as JsonSerializer<Any?>, method)
        } else {
          super.modifySerializer(config, beanDesc, serializer)
        }
      }
    })
    mapper.registerModule(module)
  }

  @Disabled("NIY")
  @Test
  internal fun `can deserialize annotated types when type specified`() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  @Disabled("NIY")
  @Test
  internal fun `can deserialize annotated types without type information when the type is registered`() {
    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
  }

  @Test
  internal fun `can serialize annotated types`() {
    val myType = MyType("someValue")
    val expected = mapper.readValue<JsonNode>("""
      {
        "method": "MyMethod.Type",
        "params": {
          "myValue": "someValue"
        }
      }
    """.trimIndent())
    assert(mapper.readValue<JsonNode>(mapper.writeValueAsString(myType))).isEqualTo(expected)
  }

  @DebugProtocolMethod("MyMethod.Type")
  private class MyType(val myValue: String)
}
