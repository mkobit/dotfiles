package io.mkobit.ssh.host

import org.junit.jupiter.api.Test
import strikt.api.Assertion
import strikt.api.expectThat
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.Path
import kotlin.io.path.div
import kotlin.script.experimental.api.ResultWithDiagnostics
import kotlin.script.experimental.api.ScriptDiagnostic
import kotlin.script.experimental.jvm.util.isIncomplete

@ExperimentalPathApi
internal class SshScriptHostTest {
  private val testDataDir = Path(System.getenv("TEST_DATA_DIR"))

  @Test
  internal fun `succeeding example`() {
    val result = evalFile(testDataDir / "example.ssh.kts")

    expectThat(result)
      .isSuccess()
  }

  @Test
  internal fun `failing example`() {
    val result = evalFile(testDataDir / "failure.ssh.kts")

    expectThat(result)
      .isFailure()
  }
}

private fun <R> Assertion.Builder<ResultWithDiagnostics<R>>.isSuccess(): Assertion.Builder<ResultWithDiagnostics.Success<R>> =
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

private fun <R> Assertion.Builder<ResultWithDiagnostics<R>>.isFailure(): Assertion.Builder<ResultWithDiagnostics.Failure> =
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

private fun <R> Assertion.Builder<ResultWithDiagnostics<R>>.isIncomplete() =
  assertThat("is incomplete", ResultWithDiagnostics<R>::isIncomplete)

private val <R> Assertion.Builder<ResultWithDiagnostics<R>>.reports: Assertion.Builder<List<ScriptDiagnostic>>
  get() = get { reports }

private val <R> Assertion.Builder<ResultWithDiagnostics.Success<R>>.value: Assertion.Builder<R>
  get() = get { value }
