package dotfilesbuild.kubernetes.kubectl

import com.mkobit.gradle.test.kotlin.testkit.runner.build
import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import strikt.api.expectCatching
import strikt.assertions.succeeded
import testsupport.gradle.newGradleRunner
import java.nio.file.Path

internal class KubectlProgramPluginTest {

  @Test
  internal fun `can configure kubectl version`(@TempDir tempDir: Path) {
    val runner = newGradleRunner(tempDir) {
      setupProjectDir {
        "build.gradle.kts" {
          content = """
            plugins {
              id("dotfilesbuild.kubernetes.kubectl.program")
            }

            kubectl {
              version.set("v1.15.2")
            }
          """.trimIndent().toByteArray()
        }
      }
    }

    expectCatching {
      runner.build("help")
    }.succeeded()
  }
}
