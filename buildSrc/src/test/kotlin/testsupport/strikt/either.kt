package testsupport.strikt

import arrow.core.Either
import strikt.api.Assertion

@Suppress("UNCHECKED_CAST")
fun <L, R, E : Either<L, R>> Assertion.Builder<E>.isRight(): Assertion.Builder<R> =
  assert("is right") {
    when {
      it.isRight() -> pass()
      it.isLeft() -> fail(actual = it, description = "was left")
    }
  }.get { this as Either.Right<R> }
    .get { b }

@Suppress("UNCHECKED_CAST")
fun <L, R, E : Either<L, R>> Assertion.Builder<E>.isLeft(): Assertion.Builder<L> =
  assert("is right") {
    when {
      it.isRight() -> fail(actual = it, description = "was right")
      it.isLeft() -> pass()
    }
  }.get { this as Either.Left<L> }
    .get { a }
