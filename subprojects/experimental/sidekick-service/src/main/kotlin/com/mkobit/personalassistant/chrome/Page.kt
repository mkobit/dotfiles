package com.mkobit.personalassistant.chrome

data class Page(
  private val description: String,
  private val devtoolsFrontendUrl: String,
  private val faviconUrl: String,
  private val id: String,
  private val parentId: String,
  private val title: String,
  private val type: String,
  private val url: String,
  private val webSocketDebuggerUrl: String
)
