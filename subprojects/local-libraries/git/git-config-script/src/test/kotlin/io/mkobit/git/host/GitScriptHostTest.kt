package io.mkobit.git.host

import io.mkobit.git.config.User
import org.junit.jupiter.api.Test
import strikt.api.expectCatching
import strikt.api.expectThat
import strikt.assertions.hasEntry
import strikt.assertions.hasSize
import strikt.assertions.isA
import strikt.assertions.isEqualTo
import strikt.assertions.isFailure
import kotlin.io.path.ExperimentalPathApi
import kotlin.io.path.Path
import kotlin.io.path.div

@ExperimentalPathApi
internal class GitScriptHostTest {
  private val testDataDir = Path(System.getenv("TEST_DATA_DIR"))

  @Test
  internal fun `simple script returning input configurations`() {
    val configurations = mapOf(
      Path(".example-git-config") to listOf(User(userName = "Guy Fieri"))
    )

    expectThat(execute(testDataDir / "simple-return.git.kts", configurations))
      .isEqualTo(configurations)
  }

  @Test
  internal fun `script creating new configuration`() {
    expectThat(execute(testDataDir / "creates-a-new-config.git.kts", emptyMap()))
      .hasSize(1)
      .hasEntry(Path(".generated-from-script"), listOf(User(userName = "Guy Fieri")))
  }

  @Test
  internal fun `script not returning anything`() {
    expectCatching {
       execute(testDataDir / "does-not-return-anything.git.kts", emptyMap())
    }.isFailure()
      .isA<IllegalArgumentException>()
  }

  @Test
  internal fun `failing script calling nonexistent function`() {
    expectCatching {
      execute(testDataDir / "failure.git.kts", emptyMap())
    }.isFailure()
      .isA<RuntimeException>()
  }
}
