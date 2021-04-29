package io.mkobit.git.host

import io.mkobit.strikt.scripting.isFailure
import io.mkobit.strikt.scripting.isSuccess
import org.junit.jupiter.api.Test
import strikt.api.expectThat
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.Path
import kotlin.io.path.div

@ExperimentalPathApi
internal class GitScriptHostTest {
  private val testDataDir = Path(System.getenv("TEST_DATA_DIR"))

  @Test
  internal fun `succeeding example`() {
    val result = evalFile(testDataDir / "example.git.kts")

    expectThat(result)
      .isSuccess()
  }

  @Test
  internal fun `failing example`() {
    val result = evalFile(testDataDir / "failure.git.kts")

    expectThat(result)
      .isFailure()
  }
}
