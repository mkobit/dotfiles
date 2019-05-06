package testsupport.strikt

import arrow.core.Option
import arrow.core.Some
import strikt.api.Assertion
import strikt.assertions.isA

fun <T> Assertion.Builder<Option<T>>.isSome(): Assertion.Builder<T> =
  assert("is Some") { it.isDefined() }
      .isA<Some<T>>()
      .get("value") { t }

fun <T> Assertion.Builder<Option<T>>.isNone() =
    assertThat("is None") { it.isEmpty() }
