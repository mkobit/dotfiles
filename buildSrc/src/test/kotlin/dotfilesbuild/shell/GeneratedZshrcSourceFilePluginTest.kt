package dotfilesbuild.shell

import com.mkobit.gradle.test.kotlin.testkit.runner.build
import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import strikt.api.expectThat
import strikt.assertions.exists
import strikt.assertions.isEmpty
import strikt.assertions.isRegularFile
import strikt.assertions.resolve
import testsupport.gradle.newGradleRunner
import testsupport.strikt.content
import testsupport.strikt.projectDir
import java.nio.file.Path

internal class GeneratedZshrcSourceFilePluginTest {
  @Test
  internal fun `zshell source file is generated and location is output to standard out`(@TempDir tempDir: Path) {
    val runner = newGradleRunner(tempDir) {
      setupProjectDir {
        "build.gradle.kts" {
          content = """
            plugins {
              id("dotfilesbuild.shell.generated-zsh")
            }
          """.trimIndent().toByteArray()
        }
      }
    }

    expectThat(runner.build("generateZshrcFile")) {
      projectDir
        .resolve("build/zsh/generated_zshrc")
        .exists()
        .isRegularFile()
        .content
        .isEmpty()
    }
  }
}
