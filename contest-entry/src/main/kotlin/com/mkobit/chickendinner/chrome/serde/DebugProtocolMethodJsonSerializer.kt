package com.mkobit.chickendinner.chrome.serde

import com.fasterxml.jackson.core.JsonGenerator
import com.fasterxml.jackson.databind.JavaType
import com.fasterxml.jackson.databind.JsonSerializer
import com.fasterxml.jackson.databind.SerializerProvider
import com.fasterxml.jackson.databind.ser.ResolvableSerializer
import com.fasterxml.jackson.databind.ser.std.StdDelegatingSerializer
import com.fasterxml.jackson.databind.ser.std.StdSerializer
import com.fasterxml.jackson.databind.type.TypeFactory
import com.fasterxml.jackson.databind.util.Converter
import com.mkobit.chickendinner.chrome.domain.DebugProtocolMethod
import java.io.ByteArrayOutputStream

internal class DebugProtocolMethodJsonSerializer(
    private val delegate: JsonSerializer<Any?>,
    private val debugProtocolMethod: DebugProtocolMethod
) : StdSerializer<Any>(null as Class<Any>?), ResolvableSerializer {
  override fun resolve(provider: SerializerProvider) {
    // From: https://stackoverflow.com/a/18405958/627727
    (delegate as ResolvableSerializer).resolve(provider)
  }

  override fun serialize(value: Any, jsonGenerator: JsonGenerator, provider: SerializerProvider) {
    // maybe use https://lewdawson.com/advanced-java-json-deserialization/
    val params = ByteArrayOutputStream().use {
      val nestedGenerator = jsonGenerator.codec.factory.createGenerator(it)
      delegate.serialize(value, nestedGenerator, provider)
      nestedGenerator.flush()
      it.toString(Charsets.UTF_8.name())
    }

    jsonGenerator.writeStartObject()
    jsonGenerator.writeStringField("method", debugProtocolMethod.method)
    jsonGenerator.writeFieldName("params")
    jsonGenerator.writeRaw(params)
    jsonGenerator.writeEndObject()
  }
}

//private data class DebugProtocolMessage(
//    val method: String,
//    val params: Any
//) {
//  constructor(debugProtocolMethod: DebugProtocolMethod, params: Any) : this(debugProtocolMethod.method, params)
//}
//
//internal class DebugProtocolMethodJsonSerializer(
//    private val debugProtocolMethod: DebugProtocolMethod
//) : StdDelegatingSerializer(object : Converter<Any, DebugProtocolMessage> {
//
//  override fun getOutputType(typeFactory: TypeFactory): JavaType {
//    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
//  }
//
//  override fun convert(value: Any): DebugProtocolMessage = DebugProtocolMessage(debugProtocolMethod, value)
//
//  override fun getInputType(typeFactory: TypeFactory?): JavaType {
//    TODO("not implemented") //To change body of created functions use File | Settings | File Templates.
//  }
//})
//
//
