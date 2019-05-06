package com.mkobit.chickendinner.chrome

import com.fasterxml.jackson.databind.JsonNode

data class ResponseFrame(
  val id: Long?,
//    val error: RequestError?,
  val result: JsonNode?,
  val method: String?,
  val params: JsonNode?
)
