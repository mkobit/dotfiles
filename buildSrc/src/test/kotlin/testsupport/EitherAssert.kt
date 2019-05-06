package testsupport

import arrow.core.Either
import org.assertj.core.api.AbstractAssert

fun <A, B> assertThat(either: Either<A, B>) = EitherAssert(either)

class EitherAssert<A, B>(actual: Either<A, B>) : AbstractAssert<EitherAssert<A, B>, Either<A, B>>(actual, EitherAssert::class.java) {

  fun hasLeftValue(value: A): EitherAssert<A, B> = apply {
    if (actual is Either.Right) {
      failWithMessage("Value is not left, but right with %s", actual.b)
    }
    (actual as Either.Left).run {
      if (a != value) {
        failWithMessage("Was left , but had value of %s (not %s)", a, value)
      }
    }
  }

  fun hasRightValue(value: B): EitherAssert<A, B> = apply {
    if (actual is Either.Left) {
      failWithMessage("Value is not right, but left with %s", actual.a)
    }
    (actual as Either.Right).run {
      if (b != value) {
        failWithMessage("Was right, but had value of %s (not %s)", b, value)
      }
    }
  }

  fun isLeftSatisfying(requirements: (A) -> Unit): EitherAssert<A, B> = apply {
    if (actual is Either.Right) {
      failWithMessage("Value is not left, but right with %s", actual.b)
    }
    (actual as Either.Left).a.let(requirements)
  }

  fun isRightSatisfying(requirements: (B) -> Unit): EitherAssert<A, B> = apply {
    if (actual is Either.Left) {
      failWithMessage("Value is not right, but left with %s", actual.a)
    }
    (actual as Either.Right).b.let(requirements)
  }
}
