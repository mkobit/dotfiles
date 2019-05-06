package com.mkobit.chickendinner.gmail

import com.google.api.services.gmail.model.Message
import kotlinx.coroutines.channels.ReceiveChannel

interface EmailRetriever {
  suspend fun retrieveEmails(): ReceiveChannel<Message>
}
