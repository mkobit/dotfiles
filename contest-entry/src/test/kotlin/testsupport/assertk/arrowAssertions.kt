package testsupport.assertk

import arrow.core.None
import arrow.core.Option
import arrow.core.Some
import arrow.core.getOrElse
import assertk.Assert
import assertk.assertions.prop
import assertk.assertions.support.expected
import assertk.assertions.support.show

fun <T> Assert<Option<T>>.isSome(valueAssertions: (Assert<T>) -> Unit) {
  val option = actual
  when (option) {
    is Some -> valueAssertions(prop("Some::t", { it.getOrElse { throw RuntimeException("can't happen") } }))
    is None -> expected("to be: Some, but was ${show(option)}")
  }
}

fun <T> Assert<Option<T>>.isNone() {
  val option = actual
  when (option) {
    is Some -> expected("to be: None, but was ${show(option)}")
  }
}
