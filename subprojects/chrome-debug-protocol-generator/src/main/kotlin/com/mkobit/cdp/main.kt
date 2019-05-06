@file:JvmName("Main")
package com.mkobit.cdp

import picocli.CommandLine
import java.nio.file.Path
import java.nio.file.Paths


object Main {
  @JvmStatic
  fun main(args: Array<String>) = CommandLine.run(Generate(), *args)
}


@CommandLine.Command(name = "Generate Chrome Debug Protocol")
private class Generate : Runnable {
  override fun run() {
    generateChromeDebugProtocol(
        ChromeDebugProtocolGenerationRequest(basePackage, protocolJson.toList(), generationDirectory)
    )
  }

  @CommandLine.Option(names = ["--basePackage"], required = true)
  var basePackage: String = ""

  @CommandLine.Option(names = ["--protocolJson"], required = true, converter = [PathConverter::class])
  var protocolJson: Array<Path> = emptyArray()

  @CommandLine.Option(names = ["--generationDir"], required = true, converter = [PathConverter::class])
  var generationDirectory: Path = Paths.get("")
}

private class PathConverter : CommandLine.ITypeConverter<Path> {
  override fun convert(value: String): Path = Paths.get(value)
}
