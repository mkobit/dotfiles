package com.mkobit.chickendinner.gmail

import com.google.api.services.gmail.model.Message
import com.google.api.services.gmail.model.MessagePart
import java.time.Instant

private fun MessagePart.findHeaderValueForName(name: String): String {
  val header = headers.find { it.name == name }
  require(header != null) {
    "Header with name $name not found in headers $headers"
  }
  return header.value
}

val Message.from: String get() = payload.findHeaderValueForName("From")
val Message.to: String get() = payload.findHeaderValueForName("To")
val Message.subject: String get() = payload.findHeaderValueForName("Subject")

val Message.internalDateTimestamp: Instant get() = Instant.ofEpochMilli(internalDate)
