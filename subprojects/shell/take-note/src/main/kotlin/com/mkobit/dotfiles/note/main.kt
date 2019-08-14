@file:JvmName("Main")
package com.mkobit.dotfiles.note

import picocli.CommandLine
import kotlin.system.exitProcess

@CommandLine.Command(
  name = "note",
  mixinStandardHelpOptions = true
)
internal class TakeNote : Runnable {

  override fun run() {
    println("hello")
  }
}

fun main(args: Array<String>) {
  val cli = CommandLine(TakeNote())
  exitProcess(cli.execute(*args))
}
