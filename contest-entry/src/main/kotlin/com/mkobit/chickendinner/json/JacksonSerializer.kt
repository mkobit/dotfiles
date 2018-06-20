package com.mkobit.chickendinner.json

import com.fasterxml.jackson.databind.ObjectMapper
import io.ktor.client.features.json.JsonSerializer
import io.ktor.client.response.HttpResponse
import io.ktor.client.response.readBytes
import io.ktor.content.OutgoingContent
import io.ktor.content.TextContent
import io.ktor.http.ContentType
import kotlin.reflect.KClass

class JacksonSerializer(val objectMapper: ObjectMapper) : JsonSerializer {
  override suspend fun read(type: KClass<*>, response: HttpResponse): Any = objectMapper.readValue(response.readBytes(), type.java)

  override fun write(data: Any): OutgoingContent = TextContent(objectMapper.writeValueAsString(data), ContentType.Application.Json)
}
