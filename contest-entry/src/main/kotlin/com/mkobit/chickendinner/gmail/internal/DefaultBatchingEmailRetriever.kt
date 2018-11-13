package com.mkobit.chickendinner.gmail.internal

import com.google.api.client.googleapis.batch.json.JsonBatchCallback
import com.google.api.client.googleapis.json.GoogleJsonError
import com.google.api.client.http.HttpHeaders
import com.google.api.services.gmail.Gmail
import com.google.api.services.gmail.model.Message
import com.mkobit.chickendinner.gmail.EmailRetriever
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.async
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.channels.ReceiveChannel
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import mu.KotlinLogging
import java.util.concurrent.atomic.AtomicInteger
import kotlin.coroutines.CoroutineContext

class DefaultBatchingEmailRetriever(
    private val gmail: Gmail,
    private val userId: String
) : EmailRetriever {

  companion object {
    private val LOGGER = KotlinLogging.logger {}
  }

  override suspend fun retrieveEmails(): ReceiveChannel<Message> {
    return withContext(Dispatchers.IO) {
      // TODO: this whole thing is awkward and most likely wrong.
      // Dealing with the batching style callback for the Google API is annoying and difficult since the callback
      // is invoked for each and every item
      LOGGER.debug { "Retrieving messages for user Id $userId" }
      val messagesResponse = gmail.users().messages().list(userId).execute()

      val callback = ChannelMessageBatchCallback(messagesResponse.messages.size)
      messagesResponse.messages.map {
        gmail.users().messages().get(userId, it.id).apply {
          format = "full"
        }
      }.fold(gmail.batch()) { batch, get ->
        get.queue(batch, callback)
        batch
      }.execute()
      callback.values
    }
  }

  private class ChannelMessageBatchCallback(
      private val totalElements: Int
  ) : JsonBatchCallback<Message>() {
    private val messageReceieveCounter = AtomicInteger()

    val values: Channel<Message> = Channel()

    override fun onSuccess(message: Message, responseHeaders: HttpHeaders) {
      GlobalScope.launch {
        try {
          values.send(message)
        } finally {
          incrementAndMaybeCloseChannel()
        }
      }
    }

    override fun onFailure(error: GoogleJsonError, responseHeaders: HttpHeaders) {
      LOGGER.error { "Error during batch get of emails: (error=$error, headers=$responseHeaders)" }
      incrementAndMaybeCloseChannel()
    }

    private fun incrementAndMaybeCloseChannel() {
      if (messageReceieveCounter.incrementAndGet() == totalElements) {
        values.close()
      }
    }
  }
}
