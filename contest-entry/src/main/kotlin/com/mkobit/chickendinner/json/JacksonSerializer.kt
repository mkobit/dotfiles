package com.mkobit.chickendinner.json

import com.fasterxml.jackson.core.type.TypeReference
import com.fasterxml.jackson.databind.ObjectMapper
import io.ktor.client.call.TypeInfo
import io.ktor.client.features.json.JsonSerializer
import io.ktor.client.response.HttpResponse
import io.ktor.client.response.readBytes
import io.ktor.content.OutgoingContent
import io.ktor.content.TextContent
import io.ktor.http.ContentType
import java.lang.reflect.Type

class JacksonSerializer(val objectMapper: ObjectMapper) : JsonSerializer {
  override suspend fun read(type: TypeInfo, response: HttpResponse): Any = objectMapper.readValue(response.readBytes(), toTypeReference(type))

  override fun write(data: Any): OutgoingContent = TextContent(objectMapper.writeValueAsString(data), ContentType.Application.Json)

  private fun toTypeReference(type: TypeInfo): TypeReference<Any> = object : TypeReference<Any>() {
    override fun getType(): Type = type.reifiedType
  }
}
