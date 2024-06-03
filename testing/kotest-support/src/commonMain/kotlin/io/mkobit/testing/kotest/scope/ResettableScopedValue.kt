package io.mkobit.testing.kotest.scope

import kotlin.properties.ReadOnlyProperty
import kotlin.reflect.KProperty

internal class ResettableScopedValue<T>(private var t: T? = null) : ReadOnlyProperty<Any?, T> {
  fun setTo(value: T) {
    t = value
  }

  fun reset() {
    t = null
  }

  val value: T get() = t ?: throw IllegalStateException("Property must not be accessed before initialization")

  override fun getValue(thisRef: Any?, property: KProperty<*>): T = value
}
