package testsupport.strikt

import arrow.core.Either
import strikt.api.Assertion

fun <L, R> Assertion.Builder<Either<L, R>>.rightWithValue(value: R) =
    assert("is right with value", value) {
      when(it) {
        is Either.Right -> {
          if (it.b == value) {
            pass()
          } else {
            fail(actual = it.b, description = "right value was actually %s")
          }
        }
        is Either.Left -> fail(actual = it.a, description = "was right with value %s")
      }
    }

fun <L, R> Assertion.Builder<Either<L, R>>.leftWithValue(value: R) =
    assert("is left with value", value) {
      when(it) {
        is Either.Right -> fail(actual = it.b, description = "was right with value %s")
        is Either.Left -> {
          if (it.a == value) {
            pass()
          } else {
            fail(actual = it.a, description = "left value was actually %s")
          }
        }
      }
    }
