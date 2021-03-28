package io.mkobit.strikt.scripting

import strikt.api.Assertion
import kotlin.script.experimental.api.ResultWithDiagnostics
import kotlin.script.experimental.api.ScriptDiagnostic

fun <R> Assertion.Builder<ResultWithDiagnostics<R>>.isSuccess(): Assertion.Builder<ResultWithDiagnostics.Success<R>> =
  assert("is success") {
    when (it) {
      is ResultWithDiagnostics.Failure -> {
        fail(
          actual = it.reports,
        )
      }
      is ResultWithDiagnostics.Success -> pass()
    }
  }.get { this as ResultWithDiagnostics.Success<R> }

fun <R> Assertion.Builder<ResultWithDiagnostics<R>>.isFailure(): Assertion.Builder<ResultWithDiagnostics.Failure> =
  assert("is failure") {
    when (it) {
      is ResultWithDiagnostics.Failure -> pass()
      is ResultWithDiagnostics.Success -> {
        fail(
          actual = it.reports,
        )
      }
    }
  }.get { this as ResultWithDiagnostics.Failure }

val <R> Assertion.Builder<ResultWithDiagnostics<R>>.reports: Assertion.Builder<List<ScriptDiagnostic>>
  get() = get { reports }

val <R> Assertion.Builder<ResultWithDiagnostics.Success<R>>.value: Assertion.Builder<R>
  get() = get { value }
