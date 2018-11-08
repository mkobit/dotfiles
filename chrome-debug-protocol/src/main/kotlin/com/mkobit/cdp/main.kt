package com.mkobit.cdp

import com.fasterxml.jackson.databind.ObjectMapper
import java.nio.file.Paths


fun main(args: Array<String>) {
  val json = ObjectMapper().readTree(
      Paths.get("/home/mkobit/dotfiles/chrome-debug-protocol/src/test/resources/browser_protocol-1.3.json").toFile()
  )
}
