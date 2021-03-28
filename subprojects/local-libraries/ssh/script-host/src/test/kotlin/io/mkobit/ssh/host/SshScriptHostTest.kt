package io.mkobit.ssh.host

import io.mkobit.strikt.scripting.isFailure
import io.mkobit.strikt.scripting.isSuccess
import org.junit.jupiter.api.Test
import strikt.api.expectThat
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.Path
import kotlin.io.path.div

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
