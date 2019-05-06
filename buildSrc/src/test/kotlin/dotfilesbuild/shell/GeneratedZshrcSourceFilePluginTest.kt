package dotfilesbuild.shell

import com.mkobit.gradle.test.kotlin.testkit.runner.build
import com.mkobit.gradle.test.kotlin.testkit.runner.setupProjectDir
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import strikt.api.expectThat
import strikt.assertions.isEmpty
import testsupport.gradle.newGradleRunner
import testsupport.strikt.content
import testsupport.strikt.exists
import testsupport.strikt.isRegularFile
import testsupport.strikt.projectDir
import testsupport.strikt.resolvePath
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

    runner.build("generateZshrcFile").let { result ->
      expectThat(result) {
        projectDir.resolvePath("build/zsh/generated_zshrc")
            .exists()
            .isRegularFile()
            .content
            .isEmpty()
      }
    }
  }
}
