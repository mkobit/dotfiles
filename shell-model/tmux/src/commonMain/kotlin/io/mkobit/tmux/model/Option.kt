package io.mkobit.tmux.model

import kotlin.jvm.JvmInline

sealed interface Option

@JvmInline
value class StringOption(val s: String) : Option {
  init {
      require(s.isNotBlank())
  }
}

fun UserOption(s: String): StringOption {
  require(s.isNotBlank())
  return StringOption("@$s")
}
