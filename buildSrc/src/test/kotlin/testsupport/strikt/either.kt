package testsupport.strikt

import arrow.core.Either
import strikt.api.Assertion

// taken from https://github.com/robfletcher/strikt/pull/164/files

@Suppress("UNCHECKED_CAST")
fun <L, R> Assertion.Builder<Either<L, R>>.isRight() =
  assert("should be Right") {
    when (it) {
      is Either.Right -> pass()
      is Either.Left -> fail()
    }
  } as Assertion.Builder<Either.Right<R>>

@Suppress("UNCHECKED_CAST")
fun <L, R> Assertion.Builder<Either<L, R>>.isRight(value: R) =
  assert("should be Right($value)") {
    when (it) {
      is Either.Right ->
        if (it.value == value) {
          pass()
        } else {
          fail()
        }

      else -> fail()
    }
  } as Assertion.Builder<Either.Right<R>>

val <R> Assertion.Builder<Either.Right<R>>.b: Assertion.Builder<R>
  @JvmName("eitherB")
  get() = get("right value") { value }

@Suppress("UNCHECKED_CAST")
fun <L, R> Assertion.Builder<Either<L, R>>.isLeft() =
  assert("should be Left") {
    when {
      it.isRight() -> fail()
      it.isLeft() -> pass()
    }
  } as Assertion.Builder<Either.Left<L>>

@Suppress("UNCHECKED_CAST")
fun <L, R> Assertion.Builder<Either<L, R>>.isLeft(value: L) =
  assert("should be Left($value)") {
    when (it) {
      is Either.Left -> {
        if (it.value == value) {
          pass()
        } else {
          fail()
        }
      }
      else -> fail()
    }
  } as Assertion.Builder<Either.Left<L>>

val <L> Assertion.Builder<Either.Left<L>>.a: Assertion.Builder<L>
  @JvmName("eitherA")
  get() = get("left value") { value }
