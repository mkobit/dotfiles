package com.mkobit.chickendinner

import io.ktor.client.HttpClient
import io.ktor.client.request.get
import io.ktor.client.request.post

suspend fun follow(client: HttpClient, userId: String) {
  val url = "https://api.twitter.com/1.1/friendships/create.json"
//  client.post<>(){  }
}
