package com.mkobit.chickendinner.chrome.serde

import com.fasterxml.jackson.databind.BeanDescription
import com.fasterxml.jackson.databind.DeserializationConfig
import com.fasterxml.jackson.databind.SerializationConfig
import com.fasterxml.jackson.databind.deser.BeanDeserializerModifier
import com.fasterxml.jackson.databind.introspect.BeanPropertyDefinition
import com.fasterxml.jackson.databind.ser.BeanPropertyWriter
import com.fasterxml.jackson.databind.ser.BeanSerializerModifier
import com.mkobit.chickendinner.chrome.domain.DebugProtocolMethod
import mu.KotlinLogging

//
//class DebugProtocolModule : SimpleModule() {
//  override fun setupModule(context: SetupContext) {
////    context.addBeanDeserializerModifier(object : BeanDeserializerModifier() {
////      override fun modifyDeserializer(
////          config: DeserializationConfig,
////          beanDesc: BeanDescription,
////          deserializer: JsonDeserializer<Any>
////      ): JsonDeserializer<Any> {
////        return if (beanDesc.classAnnotations.has(DebugProtocolMethod::class.java)) {
////          DebugProtocolMethodJsonSerializer(beanDesc.classAnnotations.get(DebugProtocolMethod::class.java), deserializer)
////        } else {
////          deserializer
////        }
////      }
////    })
//
//    context.addBeanSerializerModifier(object : BeanSerializerModifier() {
//      override fun modifySerializer(
//          config: SerializationConfig,
//          beanDesc: BeanDescription,
//          serializer: JsonSerializer<*>
//      ): JsonSerializer<*> {
//        return if (beanDesc.classAnnotations.has(DebugProtocolMethod::class.java)) {
//          DebugProtocolMethodJsonSerializer(beanDesc.classAnnotations.get(DebugProtocolMethod::class.java), serializer)
//        } else {
//          serializer
//        }
//      }
//    })
//  }
//}
//
//private class DebugProtocolMethodJsonSerializer(
//    private val debugProtocolMethod: DebugProtocolMethod,
//    private val serializer: JsonSerializer<*>
//) : JsonSerializer<Any>() {
//  override fun serialize(value: Any, gen: JsonGenerator, serializers: SerializerProvider) {
//    gen.writeStartObject(value)
//    gen.writeStringField("method", debugProtocolMethod.method)
////    gen.writeObjectField("params", serializer.serialize(value, gen, serializers))
////    gen.writeObjectField("params", value)
//    gen.writeObjectField("params", gen.codec.writeValue(gen, value))
//    gen.writeEndObject()
//  }
//}
