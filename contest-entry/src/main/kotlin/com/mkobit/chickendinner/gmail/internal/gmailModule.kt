package com.mkobit.chickendinner.gmail.internal

import com.google.api.client.extensions.java6.auth.oauth2.AuthorizationCodeInstalledApp
import com.google.api.client.extensions.jetty.auth.oauth2.LocalServerReceiver
import com.google.api.client.googleapis.auth.oauth2.GoogleAuthorizationCodeFlow
import com.google.api.client.googleapis.auth.oauth2.GoogleClientSecrets
import com.google.api.client.googleapis.javanet.GoogleNetHttpTransport
import com.google.api.client.json.jackson2.JacksonFactory
import com.google.api.client.util.store.FileDataStoreFactory
import com.google.api.services.gmail.Gmail
import com.google.api.services.gmail.GmailScopes
import org.kodein.di.Kodein
import org.kodein.di.generic.bind
import org.kodein.di.generic.factory
import org.kodein.di.generic.instance
import java.nio.file.Path

object Gmail {

  private val SCOPES = listOf(
      GmailScopes.GMAIL_LABELS,
      GmailScopes.MAIL_GOOGLE_COM
  )

  val Module = Kodein.Module(name = "Gmail") {
    bind<Gmail>() with factory { userId: String ->
      val localResourcesWorkingDirectory: Path = instance(tag = Tag.WorkspaceDirectory)
      val credentialsLocation: Path = instance(tag = Tag.CredentialsLocation)
      val transport = GoogleNetHttpTransport.newTrustedTransport()
      val jsonFactory = JacksonFactory.getDefaultInstance()
      val clientSecrets = GoogleClientSecrets.load(jsonFactory, credentialsLocation.toFile().reader())
      val localReciever = LocalServerReceiver.Builder().build()
      val authFlow = GoogleAuthorizationCodeFlow.Builder(
          transport,
          jsonFactory,
          clientSecrets,
          SCOPES
      ).setDataStoreFactory(FileDataStoreFactory(localResourcesWorkingDirectory.toFile()))
          .setAccessType("offline")
          .build()
      val authorizationApp = AuthorizationCodeInstalledApp(authFlow, localReciever)
      val credentials = authorizationApp.authorize(userId)
      Gmail.Builder(transport, jsonFactory, credentials)
          .setApplicationName("Contest Entry")
          .build()
    }
  }

  object Tag {

    /**
     * Tag for working directory to store files.
     */
    object WorkspaceDirectory

    /**
     * Tag for Gmail credentials location.
     */
    object CredentialsLocation
  }
}
