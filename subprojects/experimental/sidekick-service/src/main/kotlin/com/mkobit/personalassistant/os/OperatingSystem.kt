package com.mkobit.personalassistant.os

sealed class OperatingSystem {

  companion object {
    fun current(): OperatingSystem {
      val osName = System.getProperty("os.name")
      return when {
        osName.contains("windows") -> Windows
        osName.contains("linux") -> Linux
        else -> throw RuntimeException("Unknown OS name $osName")
      }
    }
  }

  object Windows : OperatingSystem()
  object Linux : OperatingSystem()
}
