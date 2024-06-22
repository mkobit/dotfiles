package io.mkobit.tmux.model

import kotlin.jvm.JvmInline

sealed interface OptionValue

@JvmInline
value class StringOptionValue(val s: String) : OptionValue

@JvmInline
value class IntOptionValue(val n: Int) : OptionValue

enum class OnOffOptionValue : Option {
  ON,
  OFF
}
